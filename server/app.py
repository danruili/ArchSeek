from flask import Flask

app = Flask(__name__, 
            template_folder='./../client/html'
            )
app.secret_key = 'supersecretkey'