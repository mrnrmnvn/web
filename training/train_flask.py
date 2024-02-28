from from_conll_to_hf import *
from train_function import *
from split_data import *
import os
import iuliia
from flask import Flask, render_template, redirect, url_for, request
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__)

my_output = ''

@app.route('/display_train/<filename>')
def display_train_result(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route("/", methods= ['GET', 'POST'])
def hello_world():
    return render_template('train_service.html', flag=True)


@app.route('/training', methods=['POST'])
def show_text():
    global my_output
    if request.method=='POST':
        selected_model = os.path.join(request.form.get("model_1"))
        print(selected_model)
        selected_file = request.files.get('customFile')
        sel_filename = iuliia.translate(selected_file.filename, schema=iuliia.MOSMETRO)
        current = os.getcwd()
        file_path = current + '\\' + sel_filename
        selected_file.save(os.path.join(file_path))
        print(file_path)
        selected_tags = request.form.get('yourtags')
        if selected_tags == '':
            selected_tags = 'MISSILES'
        print(selected_tags)
        try:
            training_option = request.form['training_options']
        except BadRequestKeyError:
            training_option = 'all_tags'
            
        if len(selected_tags.split(',')) == 1:
            training_option = 'all_tags'
                                
        if training_option == 'all_tags':
            my_output = 'trained_model'
            train_ner_function(file_path=file_path, tags=selected_tags, model=selected_model, output_dir=my_output)
        elif training_option == 'just_one':
            tags_separately = selected_tags.split(',')
            for tag in tags_separately:
                my_output = f'trained_model_for_{tag}'
                train_ner_function(file_path=file_path, tags=tag, model=selected_model, output_dir=my_output, nickname=f'temp_model_{tag}')

        return render_template('train_service.html', flag=True)    
    return redirect(url_for('hello_world'))

@app.route('/current_state', methods=['POST'])
def show_current_results():
    return render_template('train_service.html', flag=False)


@app.route('/hide', methods=['POST'])
def hide_it():
    return render_template('train_service.html', flag=True)
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True) 


# https://stackoverflow.com/questions/31662681/flask-handle-form-with-radio-buttons
