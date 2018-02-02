import argparse
import sys
from flask import Flask, jsonify, request
from uuid import uuid4
sys.path.append('./')
import blockchain as bc

app = Flask(__name__)
node_id = str(uuid4()).replace('-', '')
blockchain = bc.BlockChain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.pow(last_proof)
    # Deliver bonus
    blockchain.new_transaction(sender='0', # From system
                               recipient=node_id,
                               amount=1)
    block = blockchain.new_block(proof)
    response = {'message': 'New block forged',
                'index': block['index'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']}
    return jsonify(response), 200

# Use raw data format
# {
#     "sender": "6a1ce48188d64010b485dcddba06d4e1",
#     "recipient": "731e01b33dc84df49392e6079b7c1be9",
#     "amount": 1
# }
# Set Content-type to application/json
@app.route('/transaction/new', methods=['post'])
def new_transaction():
    values = request.get_json()
    keys = values.keys()
    required = ['sender', 'recipient', 'amount']
    for r in required:
        if not (r in keys):
            return 'Missing value for %s ' % r, 400
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])
    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Use raw data format
# {
#     "nodes": ["http://localhost:5000"]
# }
# Set Content-type to application/json
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force=True)
    nodes = values.get('nodes')
    if not nodes:
        return 'Error: Please supply a valid list of nodes', 400
    for node in nodes:
        blockchain.register_node(node)
    response = {'message': 'New nodes added',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conficts()
    response = {'message': 'Our chain is authoritative',
                'chain': blockchain.chain}
    if replaced:
        response['message'] = 'Our chain was replaced'
    return jsonify(response), 200

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--port',
                        help='port to listen',
                        type=int,
                        default=5000)
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    app.run(host='localhost',
            port=args.port,
            debug=True,
            threaded=True) # If not True, on Windows ther server will be fucking slow.
