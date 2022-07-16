from flask import Blueprint, flash, render_template, request, jsonify
from flask import current_app as app
from alter_igo.api import *

home_bp = Blueprint(
    'home', __name__,
    template_folder='templates',
    static_folder='static'
)

# define main route
@home_bp.route('/', methods=["GET", "POST"])
def home():
    # test database connection
    test_db()
    return render_template('icoder.html')


# define route for processing user input and generating code, output
@home_bp.route('/process')
def process():
    print('Received command!')
    command = request.args.get('command')
    print('# ' + command.strip().replace('\n', '\n# '))
    codex_context += '\n# ' + command.strip().replace('\n', '\n# ') + '\n'

    # check length of codex_context and trim if necessary
    # get positions of each command within the string, clear all but the most recent
    if len(codex_context) > 2000:
        print('Codex prompt is getting too long! Trimming...')
        command_positions = [(m.start(), m.end()) for m in re.finditer('#.+', codex_context)]
        codex_context = codex_context[command_positions[-1][0]:]

    # call openai api using code-davinci-002 to generate code from the command
    print('Calling codex API...')
    response, elapsed = codex_call(codex_context)
    print('Received response from codex API in {0:.2f} seconds.'.format(elapsed))
    codeblock = response.strip()
    print('Received code:\n')
    print(codeblock)

    # the response may be empty - we'll try one more time if so, but give up otherwise.
    if codeblock == '':
        print('No code generated! Adding a newline and trying again...')
        print('Calling codex API...')
        codex_context += '\n'
        response, elapsed = codex_call(codex_context)
        print('Received response from codex API in {0:.2f} seconds.'.format(elapsed))
        codeblock = response.strip()
        print('Received code:\n')
        print(codeblock)

        # if the returned code is still empty, remove the newline that was added and terminate
        if codeblock == '':
            print('No code generated!')
            codex_context = codex_context[:-1]
            outputs = ['string', command, '', 'No code generated!']
            
            # log results to database
            print('Logging results to database...')
            newest_id = log_commands(outputs)
            
            # update codex prompt log file
            print('Updating codex prompt...')
            with open(codex_filename, 'w') as f:
                f.write(codex_context)
            outputs.append(newest_id)

            # pass results back to client
            return jsonify(outputs=outputs)

    # if the last line is a declaration, wrap it in a print statement
    # fails if the codeblock is empty, wrap in try-except to avoid erroring out
    try:
        lastline = codeblock.splitlines()[-1]
        if ('=' not in lastline) and ('return' not in lastline) and ('print' not in lastline) and ('.fit' not in lastline):
            lastline_print = 'print(' + lastline + ')'
            codeblock = codeblock.replace(lastline, lastline_print)
            print('Caught last line as a declaration, wrapping in print statement...')
            print('Revised code:\n')
            print(codeblock)
    except IndexError:
        pass
    
    # strip leading and trailing whitespaces if included
    codex_context += codeblock + '\n'
    [outputtype, output] = runcode_raw(codeblock)
    outputs = [outputtype, command, codeblock, output]

    # write updated codex_context to file
    print('Updating codex prompt...')
    with open(codex_filename, 'w') as f:
        f.write(codex_context)
    
    # commit results to db and get id of corresponding entry
    print('Logging results to database...')
    newest_id = log_commands(outputs)

    # append id to outputs
    outputs.append(newest_id)

    return jsonify(outputs=outputs)


# define route for clearing codex prompt
@home_bp.route('/clear')
def clear():
    global codex_context, ldict
    codex_context = ''
    codex_context += '# import standard libraries\n'
    codex_context += s00
    ldict = {}
    exec(codex_context, ldict)
    return jsonify(outputs=[])

