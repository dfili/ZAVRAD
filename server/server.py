from flask import Flask, jsonify, request
from flask_cors import cross_origin, CORS
from pymongo import MongoClient, ReturnDocument
from bson import json_util
from datetime import datetime, timedelta
import random
import threading

app = Flask(__name__)
client = MongoClient('mongo', 27017)
db = client.db
CORS(app)
app.config['DEBUG'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
sem = threading.Semaphore()

# region API


@app.route('/', methods=['GET'])
@cross_origin()
def root():
    db.hits.insert_one({'time': datetime.utcnow()})
    #message = 'This page has been visited {} times.'.format(db.hits.count())
    return jsonify({'message': 'This page has been visited {} times.'.format(db.hits.count_documents({}))})


@app.route('/gantt/plan', methods=['GET'])
@cross_origin()
def get_plan():
    sem.acquire()
    clean_previous_plan_if_exists()
    result = plan_gantt_actions(1)
    sem.release()
    return jsonify({'success': result})


@app.route('/gantt/task', methods=['POST'])
@cross_origin()
def create_task():
    task_checkboxes = request.form["failed"]
    task_failed = "task_failed" in task_checkboxes
    color = 'rgb(61,185,211)'
    if task_failed:
        color = 'rgb(245, 66, 87)'
    task_id = int(get_next_sequence("task_id"))
    task_name = request.form["text"]
    end_date = request.form["end_date"]
    effects = request.form["effects"]
    task = {
        'task_id': task_id,
        'text': task_name,
        'start_date': request.form["start_date"],
        'end_date': end_date,
        'action': request.form["action"],
        'progress': float(request.form["progress"]),
        'parent': request.form["parent"],
        'duration': int(request.form["duration"]),
        'failed': task_failed,
        'preconditions': request.form["preconditions"],
        'effects': effects,
        'color': color,
        'fail_handled': False
    }
    db.tasks.insert_one(task)
    upload = []
    for e in effects.split("; "):
        if e == "":
            break
        effect_id = get_next_sequence("effect_id")
        upload.append({"effect_id": effect_id, "effect": e,
                      "task_id": task_id, "task_name": task_name, "date_acquired": end_date})
    if len(upload) != 0:
        db.effects.insert_many(upload)
    return jsonify({"action": "inserted", "tid": task_id})


@app.route('/gantt', methods=['GET'])
@cross_origin()
def get_tasks():
    sem.acquire()
    mongo_tasks = [task for task in db.tasks.find({})]
    tasks = []
    for mongo_task in mongo_tasks:
        checkboxes = []
        if mongo_task['failed']:
            checkboxes.append("step_failed")

        task = {
            'task_id': int(mongo_task['task_id']), 
            'text': mongo_task['text'],
            'start_date': mongo_task['start_date'],
            'end_date': mongo_task['end_date'],
            'action': mongo_task['action'],
            'progress': mongo_task['progress'],
            'parent': mongo_task['parent'],
            'failed': checkboxes,
            'preconditions': mongo_task['preconditions'],
            'effects': mongo_task['effects'],
            'color': mongo_task['color']
        }
        tasks.append(task)

    mongo_links = [link for link in db.links.find({})]
    links = []

    for mongo_link in mongo_links:
        link = {
            'link_id': int(mongo_link['link_id']),
            'source': mongo_link['source'],
            'target': mongo_link['target'],
            'type': str(mongo_link['type'])
        }
        links.append(link)
    sem.release()
    return json_util.dumps({'data': tasks, 'links': links})


@app.route('/gantt/task/<task_id>', methods=['PUT'])
@cross_origin()
def update_task(task_id):
    sem.acquire()
    task_checkboxes = request.form["failed"]
    task_failed = "step_failed" in task_checkboxes
    print(task_failed, flush=True)
    color = 'rgb(61,185,211)'
    fail_will_be_handled = False
    if task_failed:
        color = 'rgb(245, 66, 87)'
        preconditions = ""
        effects = get_recursive_effects(task_id)
        fail_will_be_handled = True
    else:
        preconditions = request.form["preconditions"]
        effects = request.form["effects"]

    snapshot = db.tasks.find_one({'task_id': int(task_id)})
    if snapshot:
        fail_handled = snapshot['fail_handled']
        if effects != snapshot['effects']:
            
            db.effects.delete_many({"task_id": int(task_id)})
            
            upload = []
            for e in effects.split("; "):
                if e == "":
                    break
                effect_id = get_next_sequence("effect_id")
                upload.append({"effect_id": effect_id, "effect": e,
                            "task_id": task_id, "task_name": request.form["text"], "date_acquired": request.form["end_date"]})
            if len(upload) != 0:
                db.effects.insert_many(upload)
    else: 
        fail_handled = False

    query = {"task_id": int(task_id)}
    values = {"$set": {
        'text': request.form["text"],
        'start_date': request.form["start_date"],
        'end_date': request.form["end_date"],
        'action': request.form["action"],
        'progress': float(request.form["progress"]),
        'parent': request.form["parent"],
        'duration': int(request.form["duration"]),
        'failed': task_failed,
        'preconditions': preconditions,
        'effects': effects,
        'color': color,
        'fail_handled': fail_will_be_handled
    }}

    print(query, flush=True)
    print(values, flush=True)
    db.tasks.find_one_and_update(query, values)

    if task_failed and not fail_handled:
        recalculate_plan(int(task_id))
    sem.release()
    return jsonify({"action": "updated"})


@app.route('/gantt/task/<task_id>', methods=['DELETE'])
@cross_origin()
def delete_task(task_id):
    query = {"task_id": int(float(task_id))}
    db.tasks.delete_one(query)
    db.effects.delete_many(query)
    return jsonify({"action": "deleted"})


@app.route('/gantt/link', methods=['POST'])
@cross_origin()
def add_link():
    link = {
        "link_id": get_next_sequence("link_id"),
        "source": int(request.form['source']),
        "target": int(request.form['target']),
        "type": str(int(request.form['type']))
    }
    db.links.insert_one(link)
    return jsonify({"action": "inserted", "tid": "link_id"})


@app.route('/gantt/link/<link_id>', methods=['PUT'])
@cross_origin()
def update_link(link_id):
    query = {"link_id": int(link_id)}
    values = {"$set": {
        "source": int(request.form['source']),
        "target": int(request.form['target']),
        "type": str(int(request.form['type']))
    }}
    db.links.find_one_and_update(query, values)
    return jsonify({"action": "updated"})


@app.route('/gantt/link/<link_id>', methods=['DELETE'])
@cross_origin()
def delete_link(link_id):
    query = {"link_id": int(link_id)}
    db.links.delete_one(query)
    return jsonify({"action": "deleted"})


@app.route('/actions/import', methods=['POST'])
@cross_origin()
def import_actions():
    data = request.get_json()
    action_data = data['data']  # mislim da ovoga nema u primjeru akcija
    loaded_actions = action_data['actions']

    # if the collection is empty (or does not exist) first insert initial state action and goal state action
    if "actions" not in db.list_collection_names() or db.actions.count_documents({}) == 0:
        initial_state = {
            "action_id": get_next_sequence("action_id"),
            "name": "Initial state",
            "preconditions": "",
            "effects": "",
            "time": 0,
            "price": 0
        }
        db.actions.insert_one(initial_state)
        goal_state = {
            "action_id": get_next_sequence("action_id"),
            "name": "Goal state",
            "preconditions": "",
            "effects": "",
            "time": 0,
            "price": 0
        }
        db.actions.insert_one(goal_state)

    for (action, properties) in loaded_actions.items():
        action_data = {
            "action_id": get_next_sequence("action_id"),
            "name": action,
            "preconditions": properties['preconditions'],
            "effects": properties['posteffects'],
            "time": properties['time'],
            "price": properties['price']
        }
        db.actions.insert_one(action_data)
    return jsonify({"action": "import"})


@app.route('/actions', methods=['GET'])
@cross_origin()
def get_actions():
    actions = []
    actions_data = db.actions.find()
    for action_data in actions_data:
        action = {
            "key": action_data["action_id"],
            "label": action_data["name"],
            "preconditions": action_data["preconditions"],
            "effects": action_data["effects"],
            "time": action_data["time"],
            "price": action_data["price"]
        }
        actions.append(action)
    return jsonify({"actions": actions})


@app.route('/gantt/clear')
def clear_gantt_chart():
    sem.acquire()
    clear_chart()
    sem.release()
    return jsonify({'project_cleared': True})


# od cega zelim da se efekt sastoji? ocito ime, roditeljski zadatak?
# kasnije nekad dodati zadatak koji ga je iskoristio
@app.route('/effects', methods=['GET'])
def get_effects():
    effects = []
    effects_data = db.effects.find()
    for effect_data in effects_data:
        effect = {
            "effect_id": effect_data["effect_id"],
            "effect": effect_data["effect"],
            "task_id": effect_data["task_id"],
            "task_name": effect_data["task_name"],
            "date_acquired": effect_data["date_acquired"]
        }
        effects.append(effect)
    return jsonify({"effects": effects})


# je ali sta kad razlicite akcije imaju iste postconditione
# @app.route('/effects', methods=['POST'])
# def add_effect():
#     sem.acquire()
#     # data = request.get_json() ne vucem iz requesta nego cookiesa, sessiona ili nekako drugacije
#     effects = session.get('effects')
#     effects = effects.split(" ")
#     task_id = session.get('task_id')
#     date_acquired = session.get('date_acquired')
#     upload = []
#     for e in effects:
#         effect_id = get_next_sequence("effect_id")
#         upload.append({"effect_id": effect_id, "effect": e, "task_id": task_id, "date_acquired": date_acquired})

#     db.effects.update_many(upload, upsert=True)
#     sem.release()
#     return jsonify({'effects_added': True})


@app.route('/gantt/import', methods=['POST'])
def import_existing_project():
    sem.acquire()
    data = request.get_json()
    print(data)
    # gantt_data = data['data'] # afaik, taj json ne izgleda tako, ali zasto se ovo aktivira kad radim import
    project_data = data['data']
    tasks = project_data['data']
    links = project_data['links']
    clear_chart()
    task_inserts = []
    for task in tasks:
        task_checkboxes = task["failed"]
        task_failed = "task_failed" in task_checkboxes
        color = 'rgb(61,185,211)'
        if task_failed:
            color = 'rgb(245, 66, 87)'

        start = datetime.strptime(task['start_date'], '%Y-%m-%d %H:%M')
        end = datetime.strptime(task['end_date'], '%Y-%m-%d %H:%M')

        start_date = start.strftime('%Y-%m-%d %H:%M')
        end_date = end.strftime('%Y-%m-%d %H:%M')
    # HERE
        new_task = {
            'task_id': int(get_next_sequence("task_id")),
            'text': task["text"],
            'start_date': start_date,
            'end_date': end_date,
            'action': task["action"],
            'progress': float(task["progress"]),
            'parent': task["parent"],
            # 'duration': end_date-start_date,
            'failed': task_failed,
            'preconditions': task["preconditions"],
            'effects': task["effects"],
            'color': color,
            'fail_handled': False
        }
        task_inserts.append(new_task)
    db.tasks.insert_many(task_inserts)
    link_inserts = []
    for link in links:
        new_link = {
            "link_id": get_next_sequence("link_id"),
            "source": int(link['source']),
            "target": int(link['target']),
            "type": str(int(link['type']))
        }
        link_inserts.append(new_link)
    db.links.insert_many(link_inserts)

    sem.release()
    return jsonify({'project_imported': True})


# endregion


# region utils

# HERE, ovo zadnje promijeni jer mi se cini da ovo lose radi
def get_next_sequence(name):
    sequence = db.counters.find_one_and_update(
        filter={"_id": name},
        update={"$inc": {"sequence_value": 1}},
        projection={"_id": False, "sequence_value": True},
        upsert=True,
        return_document=ReturnDocument.AFTER).get("sequence_value")
    return int(sequence)


def clear_chart():
    db.tasks.delete_many({})
    db.links.delete_many({})
    db.partial_plans.delete_many({})
    db.effects.delete_many({})
    db.counters.update_many(
        {"_id": 'link_id'}, {"$set": {"sequence_value": 0}})
    db.counters.update_many(
        {"_id": 'task_id'}, {"$set": {"sequence_value": 0}})
    db.counters.update_many(
        {"_id": 'effect_id'}, {"$set": {"sequence_value": 0}})


def clean_previous_plan_if_exists():
    db.links.delete_many({})
    db.counters.update_many({"_id": 'link_id'}, {"$set": {"sequence_value": 0}})
    db.counters.update_many({"_id": 'task_id'}, {"$set": {"sequence_value": 2}})
    query = {"task_id": {"$gt": 2}}
    db.effects.delete_many({})
    db.counters.update_many({"_id": 'effect_id'}, {
                            "$set": {"sequence_value": 0}})
    db.tasks.delete_many(query)
    db.partial_plans.delete_many({})


def parse_conditions(conditions):
    condition_objects = conditions.split("; ")
    conditions = []
    for condition_object in condition_objects:
        if condition_object == '':
            continue
        condition_value = condition_object.split(" = ")
        if len(condition_value) != 2:
            continue
        condition = {
            'name': condition_value[0].strip(),
            'value': condition_value[1].lower() == 'true'
        }
        conditions.append(condition)
    return conditions


def check_if_threat(condition, posteffects):
    is_threat = False
    for posteffect in posteffects:
        if posteffect['name'] == condition['name'] and posteffect['value'] != condition['value']:
            is_threat = True
            break
    return is_threat


def where_contains_effect(actions, condition_name, condition_value):
    valid_actions = []
    for action in actions:
        effects = action['effects']
        for effect in effects:
            if effect['name'] == condition_name and effect['value'] == condition_value:
                valid_actions.append(action)
                break
    return valid_actions


def update_action_links(has_link, source, target):
    updated_links = []
    for link in has_link:
        if link['action_id'] == source:
            link['linked_to'] = target
        if link['action_id'] == target:
            link['linked_from'] = source
        updated_links.append(link)
    return updated_links


def conditions_intersection(first, second):
    intersection = []
    for first_cond in first:
        for second_cond in second:
            if first_cond['name'] == second_cond['name'] \
                    and first_cond['value'] == second_cond['value']:
                intersection.append(first_cond)
    return intersection


def get_step(action_id, steps):
    for step in steps:
        if step['step_id'] == action_id:
            return step


def get_recursive_predecessors(order_constraints, step_id):
    recursive_predecessors = []
    direct_predecessors = [c['predecessor']['step_id'] for c in order_constraints
                           if c['successor']['step_id'] == step_id]
    recursive_predecessors.extend(direct_predecessors)
    for pred in direct_predecessors:
        preds = get_recursive_predecessors(order_constraints, pred)
        recursive_predecessors.extend(preds)

    return set(recursive_predecessors)


def get_recursive_successors(order_constraints, step_id):
    recursive_successors = []
    direct_predecessors = [c['successor']['step_id'] for c in order_constraints
                           if c['predecessor']['step_id'] == step_id]
    recursive_successors.extend(direct_predecessors)
    for pred in direct_predecessors:
        preds = get_recursive_successors(order_constraints, pred)
        recursive_successors.extend(preds)
    return set(recursive_successors)


def max_predecessor(total_order, predecessors):
    max_pred = 0
    for i in range(len(total_order)):
        if total_order[i] in predecessors:
            max_pred = i
    return max_pred


def min_successor(total_order, successors):
    min_suc = len(total_order)-1
    for i in reversed(range(len(total_order))):
        if total_order[i] in successors:
            min_suc = i
    return min_suc


def construct_total_order(partial_order):
    total_order = []
    i = 0
    for step in partial_order['steps']:
        if len(total_order) < 2:
            total_order.append(step['step_id'])
            continue
        if step['step_id'] in total_order:
            continue
        predecessors = get_recursive_predecessors(
            partial_order['ordering_constraints'], step['step_id'])
        successors = get_recursive_successors(
            partial_order['ordering_constraints'], step['step_id'])
        min_i = max_predecessor(total_order, predecessors)
        max_i = min_successor(total_order, successors)
        if min_i > max_i:
            print("There has been an error!", flush=True)
            print(step['step_id'], flush=True)
            print(total_order, flush=True)
            print(predecessors, flush=True)
            print(successors, flush=True)
        index = 0
        if min_i == max_i or min_i+1 == max_i:
            index = max_i
        else:
            index = random.randint(min_i + 1, max_i)
        total_order.insert(index, step['step_id'])

    return total_order


def construct_final_order(total_order):
    final_order = []
    order_max_i = len(total_order)
    for i in range(len(total_order)):
        if i + 1 < order_max_i:
            order = {
                'predecessor': total_order[i],
                'successor': total_order[i+1]
            }
            final_order.append(order)
    return final_order


def get_recursive_effects(task_id):
    effects = []
    current_task_id = int(task_id)
    while True:
        if current_task_id == 1:
            break
        last_link = db.links.find_one({'target': current_task_id})
        predecessor = db.tasks.find_one({'task_id': last_link['source']})
        predecessor_effects = parse_conditions(predecessor['effects'])
        for predecessor_effect in predecessor_effects:
            effect_exists = True in (
                effect['name'] == predecessor_effect['name'] for effect in effects)
            if not effect_exists:
                effects.append(predecessor_effect)

        if predecessor['failed']:
            break
        current_task_id = predecessor['task_id']

    effect_strings = []
    for effect in effects:
        effect_string = effect['name'] + " = " + str(effect['value'])
        effect_strings.append(effect_string)

    delimiter = "; "
    step_effects = delimiter.join(effect_strings)
    return step_effects


# endregion


# region recalculation
# dodati uklanjanje njegovih postconditiona iz baze
def clean_after_failed_action(failed_task):
    deleted_tasks = []
    deleted_links = []
    all_tasks_found = False
    current_failed_task = failed_task

    db.partial_plans.delete_many({})

    while not all_tasks_found:
        link_to_next = db.links.find_one(
            {'source': current_failed_task['task_id']})
        next_failed_task_id = link_to_next['target']
        next_failed_task = db.tasks.find_one({'task_id': next_failed_task_id})
        deleted_links.append(link_to_next)
        if next_failed_task['action'] == "2":
            all_tasks_found = True
        else:
            deleted_tasks.append(next_failed_task)
            current_failed_task = next_failed_task

    for task in deleted_tasks:
        db.tasks.remove({'task_id': task['task_id']})
    for link in deleted_links:
        db.links.remove({'link_id': link['link_id']})

    max_task_index = db.tasks.find().sort('task_id', -1).limit(1)
    max_link_index = db.links.find().sort('link_id', -1).limit(1)

    for max_task in max_task_index:
        db.counters.find_and_modify(
            {"_id": 'task_id'}, {"$set": {"sequence_value": max_task['task_id']}})
    for max_link in max_link_index:
        db.counters.find_and_modify(
            {"_id": 'link_id'}, {"$set": {"sequence_value": max_link['link_id']}})

    print("Done cleaning irrelevant tasks.", flush=True)


def recalculate_plan(failed_task_id):
    failed_task = db.tasks.find_one({'task_id': failed_task_id})
    clean_after_failed_action(failed_task)
    plan_gantt_actions(int(failed_task['action']))


# endregion


# region PoP


def plan_gantt_actions(initial_action):
    causal_links = []
    ordering_constraints = []
    steps = []
    goals = []
    actions = []
    db_actions = db.actions.find()

    # handling recalculation
    db_current_tasks = db.tasks.find()
    used_actions = []
    for task in db_current_tasks:
        action = int(task['action'])
        used_actions.append(action)

    # ovaj for loop vadi inicijalnu akciju i nekoristene akcije?
    for db_action in db_actions:
        if db_action['action_id'] == initial_action:
            initial_task = db.tasks.find_one({'action': str(initial_action)})
            action = {
                'action_id': db_action['action_id'],
                'name': db_action['name'],
                'preconditions': parse_conditions(initial_task['preconditions']),
                'effects': parse_conditions(initial_task['effects']),
                'time': int(db_action['time'])
            }
            actions.append(action)
            continue
        # action_exists je true ako je true unutar liste
        # koja se sastoji od true i false koji se dobiju provjerom je li trenutni action id
        # iz koristenih akcija jednak gtrenutno promatranom action idu koji gledamo u funkciji

        # tj. ovo provjerava je li trenutna akcija vec koristena
        action_used = True in [
            used_action_id == db_action['action_id'] for used_action_id in used_actions]

        # zar se to ne moze i ljepse napisati
        # action_exists = db_action['action_id'] in used_actions
        # ne 2 jer je to goal state?
        if action_used and db_action['action_id'] != 2 and db_action['action_id'] != initial_action:
            continue
        action = {
            'action_id': db_action['action_id'],
            'name': db_action['name'],
            'preconditions': parse_conditions(db_action['preconditions']),
            'effects': parse_conditions(db_action['effects']),
            'time': int(db_action['time'])
        }
        actions.append(action)
    # dodavanje pocetnog i ciljnog stanja u steps
    db_initial_state = db.tasks.find_one({'action': str(initial_action)})
    initial_step = {
        # initial state action id = 1
        'step_id': int(db_initial_state['action']),
        'preconditions': [],
        'effects': parse_conditions(db_initial_state['effects']),
        'time': int(db_initial_state['duration'])
    }
    steps.append(initial_step)

    db_goal_state = db.tasks.find_one({'action': "2"})
    goal_conditions = parse_conditions(db_goal_state['preconditions'])
    goal_step = {
        'step_id': int(db_goal_state['action']),  # goal state action id = 2
        'preconditions': goal_conditions,
        'effects': [],
        'time': int(db_goal_state['duration'])
    }
    steps.append(goal_step)

    # dodavanje conditiona u ciljna stanja
    for goal_condition in goal_conditions:
        goal_state = {
            'c': goal_condition,
            'S': goal_step
        }
        goals.append(goal_state)

    plan_problem = {
        'steps': steps,
        'ordering_constraints': ordering_constraints,
        'causal_links': causal_links,
        'successful': False
    }

    plan = partial_order_planner(plan_problem, goals, actions)
    db.partial_plans.insert_one(plan)
    if plan['successful']:
        return construct_gantt_total_order_plan(plan, initial_action)
    return False


def partial_order_planner(plan_problem, goals, actions):
    # 1. if G is empty terminate and return plan
    if len(goals) == 0:
        plan_problem['successful'] = True
        return plan_problem

    # 2. select {c,S} e G
    current_goal = random.choice(goals)
    current_goal_precondition = current_goal['c']

    # 2.a if there's a link "S[i] -(e, not c)-> S" in causal links L fail -> IMPOSSIBLE PLAN
    causal_links = plan_problem['causal_links']
    contains_contradiction = False
    for link in causal_links:
        if link['target']['step_id'] == current_goal['S']['step_id'] \
                and link['c']['name'] == current_goal_precondition['name'] \
                and link['c']['value'] != current_goal_precondition['value']:
            contains_contradiction = True

    if contains_contradiction:
        print("Contains contradiction.", flush=True)
        plan_problem['successful'] = False
        return plan_problem

    # 3. nondeterministically select step S or action with effect e
    #   if there is no such action fail -> IMPOSSIBLE PLAN
    #   otherwise update planning problem
    valid_actions = where_contains_effect(
        actions, current_goal_precondition['name'], current_goal_precondition['value'])

    valid_action_found = False
    while not valid_action_found:
        if len(valid_actions) == 0:
            print("No valid actions.", flush=True)
            plan_problem['successful'] = False
            return plan_problem

        selected_action = random.choice(valid_actions)

        if selected_action is None:
            print("Selected action is None.", flush=True)
            plan_problem['successful'] = False
            return plan_problem

        selected_step = next(
            (x for x in plan_problem['steps'] if x['step_id'] == selected_action['action_id']), None)
        if selected_step is None:
            selected_step = {
                'step_id': selected_action['action_id'],
                'preconditions': selected_action['preconditions'],
                'effects': selected_action['effects'],
                'time': selected_action['time']
            }
            plan_problem['steps'].append(selected_step)

        # Update G
        goals.remove(current_goal)
        new_goals = []
        for precondition in selected_step['preconditions']:
            new_goal = {
                'c': precondition,
                'S': selected_step
            }
            goals.append(new_goal)
            new_goals.append(new_goal)

        # Update O
        new_order = {
            'predecessor': selected_step,
            'successor': current_goal['S']
        }
        plan_problem['ordering_constraints'].append(new_order)

        # Update L
        new_causal_link = {
            'source': selected_step,
            'c': current_goal_precondition,
            'target': current_goal['S']
        }
        plan_problem['causal_links'].append(new_causal_link)

        # 4. causal link protection
        selected_step_posteffects = selected_step['effects']
        all_causal_links_protected = True
        for causal_link in causal_links:
            condition = causal_link['c']
            source = causal_link['source']
            is_threat = check_if_threat(condition, selected_step_posteffects)
            if is_threat:
                # case 1: DEMOTION -> is threat, but does not depend on source
                dependencies = conditions_intersection(
                    source['effects'], selected_step['preconditions'])
                if len(dependencies) == 0:
                    protection_order = {
                        'predecessor': selected_step,
                        'successor': causal_link['target']
                    }
                    plan_problem['ordering_constraints'].append(
                        protection_order)
                    continue

                # case 2: PROMOTION -> is threat, depends on source, target does not threaten it
                causal_link_target = causal_link['target']

                constraint_threat = {
                    'name': condition['name'],
                    'value': not condition['value']
                }

                target_threats_step = any(effect['name'] == constraint_threat['name']
                                          and effect['value'] == constraint_threat['value'] for effect in
                                          causal_link_target['effects'])

                if not target_threats_step:
                    protection_order = {
                        'predecessor': causal_link['target'],
                        'successor': selected_step
                    }
                    plan_problem['ordering_constraints'].append(
                        protection_order)
                    # temp_constraints = [c for c in plan_problem['ordering_constraints']
                    #                     if c['predecessor']['step_id'] != causal_link['source']['step_id']
                    #                     and c['successor']['step_id'] != selected_step['step_id']]
                    #
                    # plan_problem['ordering_constraints'] = temp_constraints
                    continue

                # case 3: IMPOSSIBLE PLAN
                all_causal_links_protected = False
                break

        if all_causal_links_protected:
            valid_action_found = True
        else:
            valid_actions.remove(selected_action)
            plan_problem['steps'].remove(selected_step)
            goals.append(current_goal)
            for goal in new_goals:
                goals.remove(goal)
            plan_problem['ordering_constraints'].remove(new_order)
            plan_problem['causal_links'].remove(new_causal_link)

    # 5. recursively call PoP
    return partial_order_planner(plan_problem, goals, actions)

# endregion


# region Gantt Plan


def construct_gantt_total_order_plan(partial_plan, initial_action):
    initial_task = db.tasks.find_one({'action': str(initial_action)})
    goal_task = db.tasks.find_one({'action': "2"})

    start = datetime.strptime(initial_task['end_date'], '%Y-%m-%d %H:%M')
    end = datetime.strptime(goal_task['start_date'], '%Y-%m-%d %H:%M')

    plan_duration_minutes = (end - start).total_seconds() / 60.0

    total_steps_duration = 0
    for step in partial_plan['steps']:
        step_duration = step['time']
        total_steps_duration += step_duration

    if total_steps_duration >= plan_duration_minutes:
        return False

    total_order = construct_total_order(partial_plan)
    final_order = construct_final_order(total_order)

    step_added = []
    for step_order in total_order:
        step = get_step(step_order, partial_plan['steps'])
        if step['step_id'] == initial_action or step['step_id'] == 2:
            continue

        if step['step_id'] in step_added:
            continue

        step_duration = step['time']
        step_duration_proportion = step_duration/total_steps_duration
        total_steps_duration -= step_duration

        start_limit = int(plan_duration_minutes *
                          step_duration_proportion) - step_duration
        start_minutes = random.randint(0, start_limit)

        start_date = start + timedelta(seconds=start_minutes*60)
        end_date = start_date + timedelta(seconds=step_duration*60)

        start = end_date
        plan_duration_minutes = (end - start).total_seconds() / 60.0

        step_action = db.actions.find_one({'action_id': step['step_id']})
        task_id = get_next_sequence("task_id")
        task = {
            'task_id': task_id,
            'text': step_action['name'],
            'start_date': str(start_date),
            'end_date': str(end_date),
            'action': str(int(step_action['action_id'])),
            'progress': 0.0,
            'parent': initial_task["parent"],
            'duration': step['time'],
            'preconditions': step_action["preconditions"],
            'effects': step_action["effects"],
            'failed': False,
            'color': 'rgb(61,185,211)',
            'fail_handled': False
        }
        db.tasks.insert_one(task)
        for eff in step_action["effects"].split("; "):
            effect_id = get_next_sequence("effect_id")
            structure = {"effect_id": effect_id, "effect": eff,
                      "task_id": task_id, "task_name": step_action['name'], "date_acquired": end_date}
            db.effects.insert_one(structure);          
        step_added.append(step['step_id'])

    for order in final_order:
        action_from = order['predecessor']
        action_to = order['successor']
        task_from = db.tasks.find_one({'action': str(int(action_from))})
        task_to = db.tasks.find_one({'action': str(int(action_to))})
        link = {
            'link_id': get_next_sequence('link_id'),
            'source': int(task_from['task_id']),
            'target': int(task_to['task_id']),
            'type': "0"
        }
        db.links.insert_one(link)
    return True


# endregion


if __name__ == '__main__':
    # only used locally
    app.run(host='0.0.0.0', port=8080, debug=True)
