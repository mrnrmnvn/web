def merge_them(pathh):
    
    import os
    import io
    import json 
    
    path = os.path.join(pathh)
    model_directories = os.listdir(path)
    param_files = [os.path.join(path + '\\' + directory + '\\' + 'parameters.json') for directory in model_directories]
    base_dict = {}
    for i in range(len(param_files)):
        try:
            with io.open(param_files[i], 'r', encoding='utf-8') as f:
                parameters = json.load(f)
            base_dict[f'params_{model_directories[i]}'] = parameters
        except FileNotFoundError:
            try:
                conf_path = os.path.join(path + '\\' + model_directories[i] + '\\' + 'config.json')
                trst_path = os.path.join(path + '\\' + model_directories[i] + '\\' + 'trainer_state.json')
                with open(conf_path, 'r', encoding='utf-8') as config_file, open(trst_path, 'r', encoding='utf-8') as trainer_state_file:
                    conf = json.load(config_file)
                    tr_state = json.load(trainer_state_file)

                vars = tr_state['log_history']
                vars_copy = [j for j in tr_state['log_history']]
                to_remove = []
                for j in range(len(vars)):
                    if j%2 == 0:
                        to_remove.append(vars[j])

                for not_used in to_remove:
                    vars.remove(not_used)

                best_f1 = 0
                key_index = 0
                for j in range(len(vars)):
                    if vars[j]['eval_overall_f1'] > best_f1:
                        best_f1 = vars[j]['eval_overall_f1']
                        key_index = j
                    else:
                        continue                

                new_var = vars[key_index]

                removed_index = key_index*2
                new_var_removed = vars_copy[removed_index]
                new_data = new_var_removed | new_var
                new_dump = conf | new_data

                path_to_params = os.path.join(path + '\\' + model_directories[i] + '\\' + 'parameters.json')
                with open(path_to_params, 'w', encoding='utf-8') as params_file:
                    json.dump(new_dump, params_file, indent=4)

                base_dict[f'params_{model_directories[i]}'] = new_dump
            except:
                continue
            
    final_path = os.path.join(path + '\\all_models_params.json')
    with open(final_path, 'w', encoding='utf-8') as final_file:
        json.dump(base_dict, final_file, indent=4)
    
    return final_path
