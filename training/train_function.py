from training.from_conll_to_hf import *

from transformers import AutoTokenizer, DataCollatorForTokenClassification, AutoModelForTokenClassification, TrainingArguments, Trainer, EarlyStoppingCallback, IntervalStrategy
from datasets import load_metric

import json

import os
import wandb
import io

import numpy as np

import argparse

import random
import torch


def train_ner_function(file_path:str, tags:str, model:str, where_current:str=None, export:bool=False, batch_size:int=8, num_train_epochs:float=10.0, max_steps:int=3500, weight_decay:float=1e-5, learning_rate:float=2e-5, output_dir:str='trained_model', nickname:str='temp_model', say_when:int=8, threshold:float=0.05, tf_weights=False):
    
    current = os.getcwd()
    with io.open(os.path.join(f'{os.getcwd()}\\static\\uploads\\current_results.html'), 'w', encoding='utf-8') as start_file:
        start_file.write(' ')

    print(tags)
    
    os.environ["WANDB_DISABLED"] = "true"
    
    def set_random_seed(seed):
        random.seed(seed)
        np.random.seed(seed)
        os.environ["PL_GLOBAL_SEED"] = str(seed)
        os.environ["PYTHONHASHSEED"] = str(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
     
    set_random_seed(42)
    
    main_path_in = file_path

    tg_in_t = tags
    
    tg_in = tg_in_t.split(',')

    exp_bool_in = export
    
    data_name = file_path.split('/') if '/' in file_path else file_path.split('\\')
    
    print(f'\nCREATING DATASET FROM {data_name[-1]}\n')
    
    dataset = HF_NER_dataset(mp = main_path_in, tg = tg_in, exp_bool=exp_bool_in).dataset
    print(dataset['train'])
    print(dataset['test'])
    print(dataset['validation'])

    print("List of tags: ", dataset['train'].features['ner_tags'].feature.names)
    print(f'\nFINISHED CREATING DATASET\n')
    
    label_names = dataset["train"].features["ner_tags"].feature.names

    id2label = {i: label for i, label in enumerate(label_names)}
    label2id = {v: k for k, v in id2label.items()}
    
    print(f'\nDOWNLOADING MODEL AND TOKENIZER\n')
    
    tokenizer = AutoTokenizer.from_pretrained(model, model_max_length=512, truncation=True)
    model = AutoModelForTokenClassification.from_pretrained(
        model, 
        num_labels=len(label_names),
        id2label=id2label,
        label2id=label2id,
        from_tf = tf_weights)
    
    print(f'\nMODEL USED: {model}\n')
    
    print(f'\nFINISHED DOWNLOADING\n')
    
    def tokenize_adjust_labels(all_samples_per_split):
        
        tokenized_samples = tokenizer.batch_encode_plus(all_samples_per_split["tokens"], max_length=512, truncation=True, is_split_into_words=True)
        total_adjusted_labels = []
        print(len(tokenized_samples["input_ids"]))
        for k in range(0, len(tokenized_samples["input_ids"])):
            prev_wid = -1
            word_ids_list = tokenized_samples.word_ids(batch_index=k)
            existing_label_ids = all_samples_per_split["ner_tags"][k]
            i = -1
            adjusted_label_ids = []
        
            for wid in word_ids_list:
                if(wid is None):
                    adjusted_label_ids.append(-100)
                elif(wid!=prev_wid):
                    i = i + 1
                    adjusted_label_ids.append(existing_label_ids[i])
                    prev_wid = wid
                else:
                    label_name = label_names[existing_label_ids[i]]
                    adjusted_label_ids.append(existing_label_ids[i]) 
            total_adjusted_labels.append(adjusted_label_ids)
        tokenized_samples["labels"] = total_adjusted_labels
        return tokenized_samples

    tokenized_dataset = dataset.map(tokenize_adjust_labels, batched=True)

    data_collator = DataCollatorForTokenClassification(tokenizer)

    metric = load_metric("seqeval")

    def compute_metrics(p):
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [label_names[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [label_names[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        results = metric.compute(predictions=true_predictions, references=true_labels)
        flattened_results = {
            "overall_precision": results["overall_precision"],
            "overall_recall": results["overall_recall"],
            "overall_f1": results["overall_f1"],
            "overall_accuracy": results["overall_accuracy"],
        }
        for k in results.keys():
            if(k not in flattened_results.keys()):
                flattened_results[k+"_f1"]=results[k]["f1"]

        return flattened_results

    training_args = TrainingArguments(
        output_dir=f"{current}\\{output_dir}\\{nickname}_{max_steps}",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=weight_decay,
        save_total_limit = 5,
        run_name = f"{max_steps}_{nickname}",
        evaluation_strategy=IntervalStrategy.STEPS,
        save_strategy=IntervalStrategy.STEPS,
        save_steps=200,
        logging_steps=100,
        eval_steps=100,
        max_steps=max_steps,
        seed=42,
        report_to='none',
        metric_for_best_model = 'overall_f1',
        load_best_model_at_end=True
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience = say_when, early_stopping_threshold = threshold)]
    )
    
    print("\nTRAINING STARTED!\n")
    
    where_current = os.path.join(f'{os.getcwd()}\\static\\uploads\\current_results.html')
    trainer.train(i_want_to_print=True, path_to_print=where_current)
    
    print("\nEVALUATING ON THE TEST SPLIT...")
    
    trainer.evaluate(tokenized_dataset["test"])
    
    print("\nTRAINING FINISHED!\n")
    
    if trainer.state.best_model_checkpoint is None:
        print('Данных недостаточно для обучения, модель не сохранена')
        try:
            with io.open(f'{os.getcwd()}\\static\\uploads\\current_results.html', 'w', encoding='utf-8') as f:
                f.write('Данных недостаточно для обучения, модель не сохранена')
        except:
            print('error')
    
    else:
        print(f"\nTHE BEST MODEL LOCATED AT {trainer.state.best_model_checkpoint} WITH F1 {trainer.state.best_metric}\n")
        
        
        with open(os.path.join(f'{trainer.state.best_model_checkpoint}\\config.json'), 'r', encoding='utf-8') as config_file, open(os.path.join(f'{trainer.state.best_model_checkpoint}\\trainer_state.json'), 'r', encoding='utf-8') as trainer_state_file:
            conf = json.load(config_file)
            tr_state = json.load(trainer_state_file)

        vars = tr_state['log_history']
        vars_copy = [i for i in tr_state['log_history']]
        to_remove = []
        for i in range(len(vars)):
            if i%2 == 0:
                to_remove.append(vars[i])

        for not_used in to_remove:
            vars.remove(not_used)


        for i in range(len(vars)):
            if vars[i]['eval_overall_f1'] == trainer.state.best_metric:
                key_index = i

        new_var = vars[key_index]

        removed_index = key_index*2
        new_var_removed = vars_copy[removed_index]
        new_data = new_var_removed | new_var
        new_dump = conf | new_data

        with open(os.path.join(f'{trainer.state.best_model_checkpoint}\\parameters.json'), 'w', encoding='utf-8') as params_file:
            json.dump(new_dump, params_file, indent=4)
