from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        numer = request.form.get('numer')
        if numer:
            try:
                subprocess.Popen(['python3', 'chomyk.py', numer])
                message = f'Pobieranie {numer} rozpoczęte (na serwerze).'
            except Exception as e:
                message = f'Błąd: {str(e)}'
        else:
            message = 'Nie podano numeru!'
    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
