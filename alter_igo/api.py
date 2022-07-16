# python functions for alter igo app
'''
import necessary libraries
'''
import warnings, time, os, base64, sys, re, socket, matplotlib, openai
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib_venn as v
from datetime import datetime
from flask import current_app as app
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from io import StringIO, BytesIO
from PIL import Image

'''
configure libraries and  global variables
'''
def warn(*args, **kwargs):
    pass
warnings.warn = warn
openai.api_key = os.getenv('OPENAI_API_KEY')
matplotlib.use('Agg')
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
global numtables, numplots, codex_context, error_msg, user_id, codex_filename, ldict

'''
set up variables
'''
user_id = socket.gethostname()
codex_filename = 'codex_script_' + re.sub('\.[0-9]+', '', str(datetime.now()).replace(' ', '_').replace(':', '_')) + '.txt'
old_stdout = sys.stdout
ldict = {}
numtables = 0
numplots = 0

# base string for starting off codex prompts
s00 = '''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib_venn as v
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
import shap
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split'''

# string containing all commands and code to be fed to codex API
codex_context = ''
codex_context += '# import standard libraries\n'
codex_context += s00 + '\n'

# database-related code
# set up database connection for log
db_name = 'log.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# create a class for the log table in db
class Log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(100))
    user = db.Column(db.String(100))
    command = db.Column(db.String(1000))
    codeblock = db.Column(db.String(1000))
    feedback = db.Column(db.String(1000))
    edit_ref = db.Column(db.Integer)

    def __init__(self, timestamp, command, codeblock, feedback):
        self.timestamp = timestamp
        self.user = user_id
        self.command = command
        self.codeblock = codeblock
        self.feedback = feedback
        self.edit_ref = None

# create a class for the code_edits table in db
class Code_Edits(db.Model):
    __tablename__ = 'code_edits'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(100))
    command = db.Column(db.String(1000))
    orig_code = db.Column(db.String(1000))
    edited_code = db.Column(db.String(1000))
    orig_ref = db.Column(db.Integer)

    def __init__(self, timestamp, command, orig_code, edited_code, orig_ref):
        self.timestamp = timestamp
        self.command = command
        self.orig_code = orig_code
        self.edited_code = edited_code
        self.orig_ref = orig_ref


'''
test_db() - tests connection to database
'''
def test_db():
    try:
        db.session.test_connection()
        pass
    except:
        flash('database connection failed')


'''
runcode_raw(code) - takes raw string of code, runs it, and returns the output (among other things)
'''
def runcode_raw(code):
    global numtables, numplots, error_msg
    # turn off plotting and run function, try to grab fig and save in buffer
    tldict = ldict.copy()
    plt.ioff()
    try:
        exec(code, tldict)
    except KeyError:
        pass
    except:
        print(error_msg)
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close()
    p = Image.open(buf)
    x = np.array(p.getdata(), dtype=np.uint8).reshape(p.size[1], p.size[0], -1)
    # if min and max colors are the same, it wasn't a plot - re-run as string
    if np.min(x) == np.max(x):
        new_stdout = StringIO()
        sys.stdout = new_stdout
        try:
            exec(code, ldict)
        except KeyError:
            pass
        except:
            print(error_msg)
        output = new_stdout.getvalue()
        sys.stdout = old_stdout

        # further parsing to determine if plain string or dataframe
        if bool(re.search('Index', output)):
            outputtype = 'string'
        elif bool(re.search(r'[\s]{3,}', output)):
            outputtype = 'dataframe'
            headers = re.split('\s+', output.partition('\n')[0])[1:]
            temp_df = pd.read_csv(StringIO(output.split('\n', 1)[1]), delimiter=r"\s{2,}", names=headers)
            temp_df
            if '[' in str(temp_df.index[-1]):
                temp_df.drop(temp_df.tail(1).index, inplace=True)
            output = temp_df.to_html(classes='table', table_id='table'+str(numtables), max_cols=500)
            numtables += 1
        else:
            outputtype = 'string'
        return [outputtype, output]
    # if it was a plot, then output as HTML image from buffer
    else:
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        output = "<img id='image{0}' src='data:image/png;base64,{1}'/>".format(numplots, data)
        outputtype = 'image'
        numplots += 1
        ldict.update(tldict)
        return [outputtype, output]


'''
log_commands(outputs) - takes output and other details, and logs it to the local database storing commands
'''
def log_commands(outputs):
    # unpack outputs into variables
    _, cmd, code, _ = outputs
    feedback = 'none'
    dt = str(datetime.now())
    record = Log(dt, cmd, code, feedback)
    db.session.add(record)
    db.session.commit()
    return record.id


'''
log_edit(outputs) - takes output and other details, and logs it to the local database storing edits
'''
def log_edit(edit):
    dt = str(datetime.now())
    command, orig_code, edited_code, orig_ref = edit
    record = Code_Edits(dt, command, orig_code, edited_code, orig_ref)
    db.session.add(record)
    db.session.commit()
    return record.id


'''
get_log(id) - takes id of log entry, and returns the log entry
'''
def get_log(id):
    record = Log.query.filter_by(id=id).first()
    cmd = record.command
    codeblock = record.codeblock
    return cmd, codeblock


'''
codex_call(code) - performs codex API call with a given prompt
'''
def codex_call(prompt):
    start = time.time()
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=codex_context,
        temperature=0.01,
        max_tokens=4000,
        frequency_penalty=1,
        presence_penalty=1,
        stop=["#", "'''", '"""']
        )
    end = time.time()
    elapsed = end - start
    return response['choices'][0]['text'], elapsed



