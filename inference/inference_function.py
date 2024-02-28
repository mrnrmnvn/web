def do_the_tagging(checkpoint_path, tags_in, input_text, output_dir, main_bool=True):
    import random
    from spacy import displacy
    from transformers import AutoModelForTokenClassification
    from transformers import pipeline
    from transformers import AutoTokenizer
    import io
    from razdel import sentenize
    import os
    
    new_input = (list(sentenize(input_text)))

    with io.open(os.path.join(f'{os.getcwd()}\\static\\uploads\\tagged_temp_one.html'), 'w', encoding='utf-8') as f:
        f.write('')
    
    colours = ['#FFFF00', '#CD5C5C', '#00FF00', '#00FA9A', '#4682B4', '#8A2BE2'
                  '#DDA0DD', '#F5DEB3', '#F4A460', '#B0C4DE', '#FF9999', '#FFCC99',
                  '#FFFF99', '#99FF99', '#99FFCC', '#99FFCC', '#9999FF', '#CC99FF']
    
    colors = {}
    
    used_colours = []
    if type(tags_in) == list:
        tags_inn = tags_in
    elif type(tags_in) == str:
        tags_inn = tags_in.split(',')
    for tag in tags_inn:
        rand_col = random.choice(colours)
        if rand_col not in used_colours:
            colors[tag] = rand_col
            used_colours.append(rand_col)
        else:
            rand_col = random.choice(colours)
            colors[tag] = rand_col
            used_colours.append(rand_col)
        
    def inference_ner_with_tags(checkpoint_path, tags_in, input_text, main_bool=True, colors=colors):

        tags_list = tags_in.split(',')
        NER_TAGS_TO_KEEP = tags_list
        tag_list_temp = list('O')

        for tag in NER_TAGS_TO_KEEP:
            bio_tags_out = [prefix + tag for prefix in ['B-', 'I-']]
            tag_list_temp.extend(bio_tags_out)

        label_names = sorted(tag_list_temp)
        id2label = {i: label for i, label in enumerate(label_names)}
        label2id = {v: k for k, v in id2label.items()}
        model_checkpoint = checkpoint_path

        model = AutoModelForTokenClassification.from_pretrained(
            model_checkpoint,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True
        )

        tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, model_max_length=512, truncation=True)

        token_classifier = pipeline(
            "ner", model=model, tokenizer = tokenizer,  aggregation_strategy="max"
        )
    
        pred = token_classifier(input_text)
        doc_text = input_text
        look_for = ['start', 'end', 'entity_group']

        def run_through_list(some_list:list, some_list_2:list):
            for i in range(1, (len(some_list))) :
                try:
                    if int(some_list[i-1]['end']) == int(some_list[i]['start']) and some_list[i-1]['entity_group'] == some_list[i]['entity_group']:
                        to_leave = some_list[i-1]['word']
                        new_word = to_leave + some_list[i]['word']
                        new_start = some_list[i-1]['start']
                        new_end = some_list[i]['end']
                        new_entity = some_list[i]['entity_group']
                        new_score = some_list[i]['score']
                        some_list_2[i-1] = ''
                        some_list_2[i] = {'entity_group': new_entity, 'score': new_score, 'word': new_word, 'start': new_start, 'end': new_end}
                    else:
                        some_list_2[i] = some_list[i]
                except IndexError:
                    pass
            while('' in another_list_temp):
                another_list_temp.remove('')
            return another_list_temp
        
        another_list_temp = pred        
        another_list_temp = run_through_list(pred, another_list_temp)
        final_list = another_list_temp
        final_list = run_through_list(another_list_temp, final_list)

        for element in final_list:
            if len(element['word']) <= 2:
                final_list.remove(element)

        start_end_labels = [[None for i in range(len(look_for))] for i in range(len(final_list))]

        for i in range(len(final_list)):
            for ind,val in enumerate(look_for):
                start_end_labels[i][ind] = final_list[i][val]

        entities = [final_list[i]['entity_group'] for i in range(len(final_list))]
        options = {"ents": entities, "colors": colors}
        ex = [{"text": doc_text, "ents": [{"start": x[0], "end": x[1], "label": x[2]} for x in start_end_labels]}]
        tagged_sent = displacy.render(ex, style="ent", manual=True, options=options, jupyter=False)
        if main_bool:
            return tagged_sent
        else:
            pass

    for ni in new_input:
        tagging = inference_ner_with_tags(checkpoint_path=checkpoint_path, tags_in=tags_in, input_text=ni.text.rstrip('\n'), main_bool=main_bool)
        with io.open(f'{output_dir}\\static\\uploads\\tagged_temp_one.html', 'a', encoding='utf-8') as f:
            f.write(tagging)
