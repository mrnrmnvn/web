import os
import iuliia
from flask import Flask, render_template, redirect, url_for, request
from werkzeug.exceptions import BadRequestKeyError
from pynput.mouse import Listener
import pyautogui as pag
import pyperclip
import json, io
import random
from collections import namedtuple
from labelling.json_to_conll import json_to_conll
from merging.configs_merge import merge_them
from training.from_conll_to_hf import *
from training.train_function import *
from training.split_data import *
from inference.inference_function import *
import time


app = Flask(__name__)


###################################### LABELLING ##############################################
###################################### LABELLING ##############################################
###################################### LABELLING ##############################################

start_labeling = False
tags_with_colors, my_dataset, tags, results = [], [], [], []
text_index = 0
now_tag = ''
full_text = ''
filepath_saved = ''
Acoloredtag = namedtuple('Acoloredtag', ['tag_itself', 'its_color'])
path_for_all = os.getcwd()


class MyException(Exception):
    pass


def on_click(*args):
    print(args)
    if args[-1]:
        print('The "{}" mouse key has held down'.format(args[-2].name))
    elif not args[-1]:
        print('The "{}" mouse key is released'.format(args[-2].name))
        pag.hotkey('ctrl', 'c')
        word = pyperclip.paste()
        raise MyException
    
    
def deploy_listener():
    with Listener(on_click=on_click) as listener:
        try:
            listener.join()
        except MyException:
            listener.stop()
    pag.hotkey('ctrl', 'c')
    word = pyperclip.paste()
    return word


def get_colour(): 
    r = lambda: random.randint(0,255)
    rand_col = '#%02X%02X%02X' % (r(),r(),r())
    return rand_col


@app.route('/label_base', methods= ['GET', 'POST'])
def label_base():
    global tags
    global tags_with_colors
    tags = []
    tags_with_colors = []
    return render_template('label_service.html', flag=True, display_settings=True)


@app.route('/display_while_labelling/<filename>')
def display_while_labelling(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/uploading', methods=['POST'])
def show_text():
    global my_dataset
    global text_index
    global tags
    global tags_with_colors
    global full_text
    global filepath_saved
    if request.method=='POST':
        selected_tags = request.form.get('yourtags')
        if selected_tags == '':
            selected_tags = 'MISSILES'
        tags = selected_tags.split(',') 
        for t in range(len(tags)):
            tags[t] = f"{t} {tags[t]}"
            this_tag = Acoloredtag(tags[t], get_colour())
            tags_with_colors.append(this_tag)
        selected_file = request.files.get('customFile')
        sel_filename = iuliia.translate(selected_file.filename, schema=iuliia.MOSMETRO)
        current = os.getcwd()
        file_path = current + '\\' + sel_filename
        selected_file.save(os.path.join(file_path))
        print(file_path)
        filepath_saved = file_path
        with open(os.path.join(file_path), 'r', encoding='utf-8') as ds:
            dataset = ds.read()
        full_text = dataset
        my_dataset = dataset.split('\n')
        with io.open(os.path.join(f'{path_for_all}\\static\\uploads\\the_labelled_text.html'), 'w', encoding='utf-8') as labelled_file:
            labelled_file.write('')
        return redirect(url_for('choose'))
    return redirect(url_for('label_base'))


@app.route('/uploading/choosing_tags', methods=['GET', 'POST'])
def choose():
    global my_dataset, text_index, now_tag, results, start_labeling, full_text
    if request.method=='GET':
        if start_labeling:
            word = deploy_listener().lstrip().rstrip()
            try:
                start = full_text.index(word)
                try:
                    end = start + len(word) + 1 if my_dataset[text_index][start + len(word) + 1] != ' ' else start + len(word)
                except IndexError:
                    end = start + len(word)
                entity_data = {"start": start, "end": end, "text": word, "labels": [f'{now_tag}']}
                with io.open(os.path.join(f'{path_for_all}\\static\\uploads\\the_labelled_text.html'), 'a', encoding='utf-8') as labelled_file:
                    labelled_file.write(f'<p>{word} - {now_tag}</p>')
                if entity_data not in results:
                    results.append(entity_data)
            except KeyError:
                print('string not found')
            except ValueError:
                print('string not found')
            start_labeling = False
            return render_template('label_service.html', flag=True, display_text=my_dataset[text_index], display_settings=False, tags=tags_with_colors)
        else:
            return render_template('label_service.html', flag=True, display_text=my_dataset[text_index], display_settings=False, tags=tags_with_colors)
    if request.method=='POST':
        text_index+=1
        with io.open(os.path.join(f'{path_for_all}\\static\\uploads\\the_labelled_text.html'), 'w', encoding='utf-8') as labelled_file:
            labelled_file.write('')
        results[-1]["text"] = f'{results[-1]["text"]}\n'
        try:
            next_text = my_dataset[text_index]
        except IndexError:
            next_text = 'Датасет размечен, нажмите "Завершить"'
        return render_template('label_service.html', flag=True, display_text=next_text, display_settings=False, tags=tags_with_colors)


@app.route('/uploading/choosing_tags/which_tag', methods=['POST'])
def which_tag_it_is():
    global now_tag, start_labeling
    if request.method=='POST':
        button_list = []
        for tag_button in tags:
            button_list.append(request.form.get(tag_button))
        for bb in range(len(button_list)):
            if button_list[bb] == '':
                now_tag = tags[bb][2:]
        start_labeling = True
        return redirect(url_for('choose'))
    
    
@app.route('/uploading/choosing_tags/end', methods=['POST'])
def finish_all():
    global results, filepath_saved
    pathh = os.path.join(os.getcwd())
    with open(os.path.join(f'{pathh}\\results.json'), 'w', encoding='utf-8') as fff:
        json.dump(results, fff, indent=4, ensure_ascii=False)
    path_for_conll = os.path.join(f'{pathh}\\results.txt')
    json_to_conll(filepath_saved, os.path.join(f'{pathh}\\results.json'), path_for_conll)
    return redirect(url_for('label_base'))



########################################## TRAINING #############################################
########################################## TRAINING #############################################
########################################## TRAINING #############################################

my_output = ''
Model = namedtuple('Model', ['full_path', 'relative_path'])
subfolders = [f.path for f in os.scandir('path to your models directory') if f.is_dir()]
subfolders_strip = [sub.split('\\')[-1] if '\\' in sub else sub.split('/') for sub in subfolders]
models = []
for fldr in range(len(subfolders)):
    this_model = Model(subfolders[fldr], subfolders_strip[fldr])
    models.append(this_model)

@app.route('/display_train/<filename>')
def display_train_result(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route("/training_base", methods= ['GET', 'POST'])
def training_base():
    return render_template('train_service.html', flag=True, models=models)


@app.route('/training', methods=['POST'])
def training_options():
    global my_output
    if request.method=='POST':
        selected_model = os.path.join(request.form.get("model_1"))
        selected_file = request.files.get('customFile')
        sel_filename = iuliia.translate(selected_file.filename, schema=iuliia.MOSMETRO)
        current = os.getcwd()
        file_path = current + '\\' + sel_filename
        selected_file.save(os.path.join(file_path))
        selected_tags = request.form.get('yourtags')
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

        return render_template('train_service.html', flag=True, models=models)    
    return redirect(url_for('training_base'))

@app.route('/current_state', methods=['POST'])
def show_current_results():
    return render_template('train_service.html', flag=False, models=models)


@app.route('/hide', methods=['POST'])
def hide_it():
    return render_template('train_service.html', flag=True, models=models)




############################################# INFERENCE #########################################
############################################# INFERENCE #########################################
############################################# INFERENCE #########################################


@app.route('/display/<filename>')
def display_semantic_result(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route("/inference_base", methods= ['GET', 'POST'])
def inference_base():
    return render_template('inf_service.html', flag=True, models=models)

@app.route('/inference', methods=['POST'])
def inf_inference():
    global path_for_all
    if request.method=='POST':
        selected_model_path = request.form.get("model_1")
        selected_file = request.files.get('customFile')
        sel_filename = iuliia.translate(selected_file.filename, schema=iuliia.MOSMETRO)
        current = os.getcwd()
        file_path = current + '\\' + sel_filename
        selected_file.save(os.path.join(file_path))
        with open(os.path.join(file_path), 'r', encoding='utf-8') as f:
            text = f.read()
        with io.open(os.path.join(fr'{selected_model_path}\config.json'), 'r', encoding='utf-8') as configfile:
            config = json.load(configfile)
        selected_tagss = config["id2label"]
        selected_tags_list = []
        for i in range(len(selected_tagss)):
            tag = selected_tagss[str(i)]
            if 'B-' in tag:
                tag = tag.lstrip('B-')
            elif 'I-' in tag:
                tag = tag.lstrip('I-')
            if tag not in selected_tags_list and tag != "O":
                selected_tags_list.append(tag)
        selected_tags = ','.join(selected_tags_list)
        do_the_tagging(checkpoint_path=selected_model_path, tags_in=selected_tags, input_text=text, output_dir=path_for_all)
        return render_template('inf_service.html', flag=False, models=models)    
    return redirect(url_for('inference_base'))



###################################### MERGING ########################################
###################################### MERGING ########################################
###################################### MERGING ########################################

my_output = ''

@app.route('/display/<filename>')
def display_that_finished(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route("/merging_base", methods= ['GET', 'POST'])
def merging_base():
    return render_template('merge_service.html', flag=True)


@app.route('/merging', methods=['POST'])
def start_merging():
    global my_output
    if request.method=='POST':
        selected_model = os.path.join(request.form.get("model_path"))
        print(selected_model)
        where_is = merge_them(selected_model)
        return render_template('merge_service.html', where_is=where_is, flag=False)    
    return redirect(url_for('merging_base'))





######################################### ALL IN ONE ######################################
######################################### ALL IN ONE ######################################
######################################### ALL IN ONE ######################################

buttons = []

@app.route("/", methods= ['GET', 'POST'])
def all_here():
    global buttons
    if request.method=='GET':
        return render_template('full_ner.html', flag=True, display_settings=True)
    elif request.method=='POST':
        button_list = []
        for service_button in buttons:
            button_list.append(request.form.get(service_button))
        for bb in range(len(button_list)):
            if button_list[bb] == '':
                print(f'i pressed {buttons[bb]}')
                now_tag = buttons[bb][2:]
        

@app.route("/back", methods=['POST'])
def back_home():
    if request.method=='POST':
        return redirect(url_for('all_here'))
        
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070, debug=True) 

