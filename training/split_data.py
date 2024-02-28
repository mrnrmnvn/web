def add_b(NER_TAGS_TO_KEEP: list):
    
    b_tags = []
    for tag in NER_TAGS_TO_KEEP:
        b_tag = 'B-' + tag
        b_tags.append(b_tag)

    return b_tags

def count_tags(all_lines:list, b_tags: list):
    
    b_sample = dict()
    
    for tag in b_tags:
        b_sample[tag] = 0
        
    for line in all_lines:
        for tag in b_tags:
            if tag in line:
                b_sample[tag] += 1

    return b_sample

def to_keep(NER_TAGS_TO_KEEP):
    
    tag_list_temp = list('O')
    for tag in NER_TAGS_TO_KEEP:
        bio_tags_out = [prefix + tag for prefix in ['B-', 'I-']]
        tag_list_temp.extend(bio_tags_out)
    
    ner_tags_to_keep = set(tag_list_temp)
    return ner_tags_to_keep


def do_the_splits(PATH_TO_YOUR_DATA: str, NER_TAGS_TO_KEEP: list, useless=False) -> list:
    
    import os
    
    with open(os.path.join(PATH_TO_YOUR_DATA), encoding='utf-8') as f:
        
        all_lines = f.readlines()
        # all_lines = to_keep(all_lines_orig, NER_TAGS_TO_KEEP)
        
        b_tags = add_b(NER_TAGS_TO_KEEP)
        tag_occurence_dict = count_tags(all_lines, b_tags)
        ner_tags_to_keep = to_keep(NER_TAGS_TO_KEEP)
                    
        # этот блок делит датасет на тексты
        real_all = []
        for v in all_lines:
            temp_str = v.replace(' -X- _ ', ' ')
            if temp_str != '\n' and temp_str.split()[-1] not in ner_tags_to_keep:
                temp_l = temp_str.split()
                temp_l[-1] = 'O'
                temp_str = ' '.join(temp_l) + '\n'
            elif v == '\n':
                temp_str = '\n|'
            real_all.append(temp_str)
        all1 = ''.join(real_all)
        all_texts = all1.split('|') 
        
        print(tag_occurence_dict)
        print('NOTE: the list of occurences was counted before removing duplicates', '\n')
        
        # тренировочный список, временный список для записи строк и список лишнего
        d_train = []
        temp_list = []
        extra = []
        
        # берем по одному наши тэги:
        for tag in b_tags:
            tag_extra = []
            counter = 0                # счетчик тэгов, которые уже есть внутри датасета
            occurences = tag_occurence_dict[tag]     # наxодим в словаре количество вхождений
            maximum = int(int(occurences) * 0.8)    # вычисляем допустимый максимум
            
            # берем по одному тексты:
            for text in all_texts:
                tags_in_text = 0         # количество тэгов в текущем тексте
                if text in temp_list and tag in text:
                    already_there = text.count(tag)
                    counter += already_there
                elif text not in temp_list and text not in extra:     # текст интересует нас, только если его еще не было в датасете и он не был отправлен в лишние тексты
                    if tag in text:          # смотрим на текст только если в нем есть текущий тэг
                        tags_in_text = text.count(tag)
                    if (counter + tags_in_text) < maximum:
                        temp_list.append(text)
                        counter += tags_in_text
                    elif (counter + tags_in_text) >= maximum:
                        tag_extra.append(text)
            extra.extend(tag_extra)
            
        for string in extra:
            if string == '':
                extra.remove(string)
        
        extra = list(set(extra))
        
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # чтобы посчитать вхождения после удаления дубликатов        
        unique_texts_list = list(set(all_texts))
        empty_list = []
        for utl in unique_texts_list:
            empty_list.extend(utl.split('\n'))
        
        unique_count = count_tags(empty_list, b_tags)
        print(unique_count)
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        
        print('total texts: ', len(all_texts))
        print('unique texts: ', len(set(all_texts)))
        
        for t in temp_list:
            if t not in extra:
                d_train.append(t)
        d_train_set = set(d_train)
        print('train texts before verification: ', len(d_train_set))
        print('extra texts before verification: ', len(extra), '\n')
            
        b_tags = add_b(NER_TAGS_TO_KEEP)
    
        train = list(d_train_set)
        
        train_lines = []
        for train_text in train:
            ttl = train_text.split()
            train_lines.append(ttl)
            
        train_samples = count_tags(train_lines, b_tags)
        tag_occurence_dict = count_tags(all_lines, b_tags)
                
        temporary = []
        for tag in b_tags:
            twt = 0
            twt_list = []
            for tt in train:
                if tag in tt and tt not in temporary:
                    twt += tt.count(tag)
                    twt_list.append(tt)
            portion = train_samples[tag] / tag_occurence_dict[tag]
            if portion > 0.8:
                diff = 0.8 - portion
                to_cut = int(diff * len(twt_list))
                temporary.extend(twt_list[:to_cut])
                extra.extend(twt_list[to_cut:])
            else:
                temporary.extend(twt_list)
        
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # # поскольку тэг event нравномерно распределялся по выборкам:
        # without_event = [w for w in b_tags if w != 'B-EVENT']
        # event_only = []
        # event_counter = 0
        # for text in texting:
        #     if "B-EVENT" in text:
        #         event_counter += 1
        #         if all([True if tag not in text else False for tag in without_event]):
        #             event_only.append(text)
        
        # for ev in event_only:
        #     extra.append(ev)
        #     if ev in temporary:
        #         temporary.remove(ev)            
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
                
        for text in train:
            if text not in temporary and text not in extra:
                extra.append(text)
        
        extra = list(set(extra))
        temporary = list(set(temporary))
        
        for t in temporary:
            if t in extra or t == '':
                temporary.remove(t)
        for e in extra:
            if e in temporary:
                extra.remove(e)
                
        print('train texts after verification: ', len(temporary))
        print('texts for 2nd and 3rd splits: ', len(extra), '\n')
        
    # return temporary, extra
    
        final_lines = []
        for temp_text in temporary:
            final_lines.extend(temp_text.split())

        final = count_tags(final_lines, b_tags)
        print(final, '\n')
                    
        for tag in b_tags:
            a = final[tag] / tag_occurence_dict[tag]
            print(tag, a)

        
        lines_list = []
        for lfl in extra:
            lines_list.extend(lfl.split('\n'))
        extra_sample = count_tags(lines_list, b_tags)
        print(extra_sample)                
                    
        testsplit = []
        valid = []
        for tag in b_tags:
            tag_valid = []
            counter = 0                # счетчик тэгов, которые уже есть внутри датасета
            occurences = extra_sample[tag]     # наxодим в словаре количество вхождений
            maximum = int(int(occurences) * 0.5)    # вычисляем допустимый максимум
                
        # берем по одному тексты:
        for text in extra:
            tags_in_text = 0         # количество тэгов в текущем тексте
            if text in testsplit and tag in text:
                already_there = text.count(tag)
                counter += already_there
            elif text not in testsplit and text not in valid:      # текст интересует нас, только если его еще не было в датасете и он не был отправлен в лишнее
                if tag in text:          # смотрим на текст тоолько если в нем есть текущий тэг
                    tags_in_text = text.count(tag)
                    if (counter + tags_in_text) < maximum:
                        testsplit.append(text)
                        counter += tags_in_text
                    elif (counter + tags_in_text) >= maximum:
                        tag_valid.append(text)
        valid.extend(tag_valid)
        
        divide = []
        for text in extra:
            if text not in valid and text not in testsplit:
                divide.append(text)
        
        for i in range(len(divide)):
            if i % 2 == 0:
                valid.append(divide[i])
            else:
                testsplit.append(divide[i])
        
        if len(testsplit) == 0:
            for i in range(len(valid)):
                if valid[i] == '':
                    continue
                else:
                    text_in_question = valid[i]
                    break
            testsplit.append(text_in_question)
            valid.remove(text_in_question)
        
        
        valid = list(set(valid))
        testsplit = list(set(testsplit))
        
        print('\n', len(temporary), len(testsplit), len(valid), '\n', ner_tags_to_keep)
        
    training = []
    valid_lines =[]
    test_lines = []
    for tr in temporary:
        training.extend(tr.split('\n'))
    if '' in training:
        training.remove('')
    for vl in valid:
        valid_lines.extend(vl.split('\n'))
    if '' in valid_lines:
        valid_lines.remove('')
    for tl in testsplit:
        test_lines.extend(tl.split('\n'))
    if '' in test_lines:
        test_lines.remove('')

    for i in range(len(training)):
        training[i] = f'{training[i]}\n'
    for i in range(len(valid_lines)):
        valid_lines[i] = f'{valid_lines[i]}\n'
    for i in range(len(test_lines)):
        test_lines[i] = f'{test_lines[i]}\n'
    
    return training, valid_lines, test_lines, ner_tags_to_keep
