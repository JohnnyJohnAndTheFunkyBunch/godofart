#!flask/bin/python
from flask import Flask
from flask import jsonify
from flask import request
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

edges = set()
nodes = set()
uids = []
highest_id = 0

@app.route('/')
def index():
    return "Hello, World!"

##################
#  Device calls  #
##################


@app.route('/api/register', methods=['POST'])
def register_node():
    global highest_id
    global uids
    global nodes
    if not uids:
        nodes.add(highest_id)
        highest_id = highest_id + 1
        socketio.emit('register',{'id': highest_id - 1})
        return jsonify({'id': highest_id - 1})
    else:
        newid = uids.pop()
        nodes.add(newid)
        socketio.emit('register',{'id': newid})
        return jsonify({'id': newid})

@app.route('/api/unregister', methods=['POST'])
def unregister_node():
    global highest_id
    global uids
    global nodes
    global edges
    removed_edges = set()
    myid=int(request.form['id'])
    if(myid in nodes):
        nodes.remove(myid)
        for edge in edges:
            if (myid in edge):
                removed_edges.add(edge)
        for edge in removed_edges:
            edges.remove(edge)
        uids.append(myid)
        socketio.emit('unregister',{'id': myid})
        return jsonify({'node': myid, 'edges': list(removed_edges)})
        # remove all edges containing that
    else:
        return jsonify({'error': 'node does not exist'})

@app.route('/api/link', methods=['POST'])
def link():
    global highest_id
    global nodes
    global edges
    global uids
    myid=int(request.form['id'])
    nid=int(request.form['nid'])
    if (myid in nodes and nid in nodes):
        if (myid < nid) :
            edges.add((myid,nid))
            socketio.emit('link',{'edge':(myid,nid)})
            return jsonify({'edge':(myid,nid)})
        elif (myid > nid):
            edges.add((nid,myid))
            socketio.emit('link',{'edge':(nid,myid)})
            return jsonify({'edge':(nid,myid)})
        else:
            return jsonify({'error': "same node"})
    return jsonify({'error': "one of the nodes not found"})

@app.route('/api/unlink', methods=['POST'])
def unlink():
    global highest_id
    global nodes
    global edges
    global uids
    try:
        myid=int(request.form['id'])
        nid=int(request.form['nid'])
        if (myid < nid) :
            edges.remove((myid,nid))
            socketio.emit('unlink',{'edge':(myid,nid)})
            return jsonify({'edge':(myid,nid)})
        elif (myid > nid):
            edges.remove((nid,myid))
            socketio.emit('unlink',{'edge':(nid,myid)})
            return jsonify({'edge':(nid,myid)})
        else:
            return jsonify({'error': "same node"})
    except Exception, e:
        return jsonify({'error': repr(e)})

#####################
#  Front end calls  #
#####################

@app.route('/api/graph', methods=['GET'])
def get_graph():
    return jsonify({'nodes':list(nodes), 'edges': list(edges)})

@app.route('/api/edges', methods=['GET'])
def get_edges():
    return jsonify({'edges': list(edges)})

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': list(nodes)})

#################
#  Admin Calls  #
#################
@app.route('/api/restart', methods=['POST'])
def restart():
    global highest_id
    global nodes
    global edges
    global uids
    edges.clear()
    nodes.clear()
    uids = []
    highest_id = 0
    socketio.emit('graph', {'nodes':list(nodes), 'edges': list(edges)})
    return jsonify({'message': "success"})

@app.route('/api/clearedges', methods=['GET'])
def clear_edges():
    global edges
    edges.clear()
    socketio.emit('graph', {'nodes':list(nodes), 'edges': list(edges)})
    return jsonify({'message': "success"})

@app.route('/api/clearnodes', methods=['GET'])
def clear_nodes():
    global nodes
    nodes.clear()
    socketio.emit('graph', {'nodes':list(nodes), 'edges': list(edges)})
    return jsonify({'message': "success"})

################
#  Web Socket  #
################

@socketio.on('connect')
def connect():
    print('=====================Client connected=================')
    emit('graph', {'nodes':list(nodes), 'edges': list(edges)})


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
