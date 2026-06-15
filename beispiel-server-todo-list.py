"""
Requirements:
* flask
"""

import uuid
from flask import Flask, request, jsonify, abort

# initialize Flask server
app = Flask(__name__)

# Test Daten
"""
# create unique id for lists, entries
todo_list_1_id = '1318d3d1-d979-47e1-a225-dab1751dbe75'
todo_list_2_id = '3062dc25-6b80-4315-bb1d-a7c86b014c65'
todo_list_3_id = '44b02e00-03bc-451d-8d01-0c67ea866fee'
todo_1_id = uuid.uuid4()
todo_2_id = uuid.uuid4()
todo_3_id = uuid.uuid4()
todo_4_id = '1318d3d1-d979-47e1-a225-dab1751dbe77'

# define internal data structures with example data
todo_lists = [
    {'id': todo_list_1_id, 'name': 'Einkaufsliste'},
    {'id': todo_list_2_id, 'name': 'Arbeit'},
    {'id': todo_list_3_id, 'name': 'Privat'},
]
todos = [
    {'id': todo_1_id, 'name': 'Milch', 'description': '', 'list': todo_list_1_id},
    {'id': todo_2_id, 'name': 'Arbeitsblätter ausdrucken', 'description': '', 'list': todo_list_2_id},
    {'id': todo_3_id, 'name': 'Kinokarten kaufen', 'description': '', 'list': todo_list_3_id},
    {'id': todo_4_id, 'name': 'Eier', 'description': '', 'list': todo_list_1_id},
]
"""

todo_lists = {}
todos = {}

# add some headers to allow cross origin access to the API on this server, necessary for using preview in Swagger Editor!
@app.after_request
def apply_cors_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# define endpoint for getting and deleting existing todo lists
@app.route('/todo-list/<list_id>', methods=['GET', 'DELETE','POST'])
def handle_list(list_id):
    # find todo list depending on given list id
    list_item = None
    for l in todo_lists:
        if l['id'] == list_id:
            list_item = l
            break
    # if the given list id is invalid, return status code 404
    if not list_item:
        abort(404, jsonify('List with the ID {'+list_id+'} does not exist.'))
    if request.method == 'GET':
        # find all todo entries for the todo list with the given id
        print('Returning todo list...')
        return jsonify([i for i in todos if i['list'] == list_id])
    elif request.method == 'DELETE':
        # delete list with given id
        print('Deleting todo list...')
        todo_lists.remove(list_item)
        return jsonify('List deleted.'), 204
    elif request.method == 'POST':
        print('Add todo list...')
        new_item = request.get_json(force=True)
        new_todoId = str(uuid.uuid4())
        newObject = {'id': new_todoId, 'name': new_item['name'] , 'description': new_item['description'] , 'list': list_id}
        todos.append(
            newObject
        )
        print(newObject)
        return newObject, 201

# define endpoint for adding a new list
@app.route('/todo-list', methods=['POST'])
def add_new_list():
    # make JSON from POST data (even if content type is not set correctly)
    new_list = request.get_json(force=True)
    if(new_list['name'] == ''):
        abort(406, jsonify('Request contains faulty Data.'))
    # create id for new list, save it and return the list with id
    new_todoList = {'id': str(uuid.uuid4()), 'name': new_list['name']}
    todo_lists.append(new_todoList)
    return jsonify(new_todoList), 201

"""
# define endpoint for getting all lists
@app.route('/todo-list', methods=['GET'])
def get_all_lists():
    print('Returning all todo lists...')
    return jsonify(todo_lists)
"""

@app.route('/entry/<entry_id>', methods=['PATCH', 'DELETE'])
def handle_entry(entry_id):
    # find todo list depending on given list id
    entry_item = None
    for l in todos:
        if l['id'] == entry_id:
            entry_item = l
            break
    # if the given entry id is invalid, return status code 404
    if not entry_item:
        abort(404, jsonify('Entry with the ID {'+entry_id+'} does not exist.'))
    if request.method == 'PATCH':
        # Updates entries for the entry with the given id
        print('Update entry...')
        new_item = request.get_json(force=True)
        newObject =  {'id': entry_id, 'name': new_item['name'], 'description': new_item['description'], 'list': entry_item['list']}
        entry_item.update(newObject)

        return jsonify(newObject), 200
    elif request.method == 'DELETE':
        # delete entry with given id
        print('Deleting entry...')
        todos.remove(entry_item)
        return jsonify('Entry deleted.'), 204

if __name__ == '__main__':
    # start Flask server
    app.debug = True
    app.run(host='0.0.0.0', port=5000)