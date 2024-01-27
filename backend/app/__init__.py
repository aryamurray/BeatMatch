from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
    
# app instance
app = Flask(__name__)
CORS(app)

@app.route('/home', methods=['GET'])
def home():
    return {"members": ["Member1", "Member2", "Member3"]}

if __name__ == '__main__':
    app.run(debug=True, port=8080)