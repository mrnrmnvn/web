def json_to_conll(initial_file, flask_file, conll_filepath):
    import json, os

    with open(os.path.join(initial_file), 'r', encoding='utf-8') as orig:
        original_file = orig.read()

    with open(os.path.join(flask_file), 'r', encoding='utf-8') as jsonchik:
        json_file = json.load(jsonchik)
        
    print('ok')
    
    with open(os.path.join(conll_filepath), 'w', encoding='utf-8') as conll_file:
        for i in range(len(json_file)):
            starting_point = json_file[i]['start']
            ending_point = json_file[i]['end']
            current_text = json_file[i]['text']
            its_label = json_file[i]['labels'][0]
            try:
                if json_file[i-1]['labels'] != json_file[i]['labels']:
                    prefix = 'B-' 
                elif json_file[i-1]['labels'] == json_file[i]['labels'] and json_file[i-1]['end'] + 1 != json_file[i]['start']:
                    prefix = 'B-'
                elif json_file[i-1]['labels'] == json_file[i]['labels'] and json_file[i-1]['end'] + 1 == json_file[i]['start']:
                    prefix = 'I-'
            except IndexError:
                prefix = 'B-'

            if len(current_text.split(' ')) > 1:
                deassembling = current_text.split(' ')
                for j in range(len(deassembling)):
                    to_add_a_slashn = False
                    if deassembling[j].endswith('\n'):
                        deassembling[j] = deassembling[j].replace('\n', '')
                        to_add_a_slashn = True
                    if j == 0 and prefix == 'B-':
                        entity_info = ' -X- _ ' + prefix + its_label + '\n'
                    else:
                        entity_info = ' -X- _ ' + 'I-' + its_label + '\n'
                    if to_add_a_slashn:
                        entity_info = entity_info + '\n'
                    deassembling[j] = deassembling[j] + entity_info
                reassembled = ''.join(deassembling)
                print(reassembled)
                conll_file.write(reassembled)
            else:
                entity_info = ' -X- _ ' + prefix + json_file[i]['labels'][0] + '\n'
                if json_file[i]['text'].endswith('\n'):
                    my_string = json_file[i]['text'].replace('\n', '')
                    replace_with = my_string + entity_info + '\n'
                else:
                    replace_with = json_file[i]['text'] + entity_info
                print(replace_with)
                conll_file.write(replace_with)
                
            try:    
                inbetween = original_file[ending_point:json_file[i+1]['start']]
                inbetween_split = inbetween.split()
                for ibw in range(len(inbetween_split)):
                    inbetween_split[ibw] = f"{inbetween_split[ibw]} -X- _ O\n"
                ibww = ''.join(inbetween_split)
                conll_file.write(ibww)
            except IndexError:
                inbetween = original_file[ending_point:]
                inbetween_split_til_new_text = inbetween.split('\n')[0]
                inbetween_split = inbetween_split_til_new_text.split()
                for ibw in range(len(inbetween_split)):
                    inbetween_split[ibw] = f"{inbetween_split[ibw]} -X- _ O\n"
                ibww = ''.join(inbetween_split)
                conll_file.write(ibww)