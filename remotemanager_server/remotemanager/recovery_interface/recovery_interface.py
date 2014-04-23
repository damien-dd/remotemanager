from flask import Flask, request, render_template, redirect
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('main.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0')
