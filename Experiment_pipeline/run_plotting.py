from collections import Counter

import numpy as np
import plotly.graph_objects as go

import exportFigure
from DataAnalysis.Evaluation.scoring_modular import score_single_best_solver, f2_par2_cluster, f1_par2, \
    f3_weigh_with_cluster_size
from DataFormats.DbInstance import DbInstance
from Experiment_pipeline.run_experiments import read_experiment_json, read_evaluation_json


# gets the evaluations (or experiments) depending on the given settings_dict from the input_file
# the settings dict, needs to have the same structure as the dict stored in "settings" in the input file,
# however instead of values, for each settings list of settings is used, to enable the usage of "or"
# example: In the file the structure of the problem is given as {settings: {"scaling_algorithm": "SCALEMINUSPLUS1" }}
# then the settings dict needs to hve the structure: {"scaling_algorithm": ["SCALEMINUSPLUS1"] }, we can especially use
# {"scaling_algorithm": ["SCALEMINUSPLUS1", "NORMALSCALE"] } to select evaluations with different scaling algorithm

# returns the list of evaluations that fit the dict and a diff which contains all keys, that where missing in the
# settings_dict, but where present in at least one selected evaluation
def collect_evaluation(input_file, settings_dict):
    data = read_evaluation_json(input_file)
    collected_evaluation = []
    diff_set = set()
    for evaluation in data:
        matchingValues = True
        for key, value in settings_dict.items():
            if evaluation['settings'][key] not in value:
                matchingValues = False
                break

        if matchingValues:
            collected_evaluation.append(evaluation)
            diff = evaluation['settings'].keys() - settings_dict.keys()
            diff_set = set.union(diff_set, diff)

    return collected_evaluation, diff_set


# ----------------------------------------------------------------------------------------------------------------------

# Plots a circle diagram of the distribution of the best single solver
# input_file_bss: The file to read the beast single solver data from
# output_file: The filename of the exported html (no export if equal to '')
# show_plot: If the plot should be opened in the browser after running the function
def plot_par2_bss_distribution(input_file_bss, output_file='', show_plot=False):
    result_bss = read_evaluation_json(input_file_bss)
    best_solver = []
    for key, item in result_bss[1].items():
        best_solver.append(item[0][0][0])

    counter = Counter(best_solver)

    keys = []
    values = []
    for key, value in counter.items():
        keys.append(key)
        values.append(value)

    fig = go.Figure(data=[go.Pie(labels=keys,
                                 values=values)],
                    layout=go.Layout(
                        title=go.layout.Title(
                            text='Distributions of solvers if each instance uses the best single solver'))
                    )

    if output_file != '':
        exportFigure.export_plot_as_html(fig, output_file)

    if show_plot:
        fig.show()


# Example

# plot_par2_bss_distribution('bss', show_plot=True)

# ----------------------------------------------------------------------------------------------------------------------

# Creates a bar chart of the solvers with the best mean par2 scores and for comparison the best single solver (bss)
# input_file_par2_scores: The file to read the par2 scores from
# input_file_bss: The file to read the bss scores from
# plot_description: The title/description of the plot
# max_cluster_amount: Splits the colors of the best par2 scores by the amount of clusters where max_cluster_amount
# is the border. Can be useful to see which clusters are overfitted
# cutoff: How many evaluation instances should be maximal shown
# output_file: The filename of the exported html (no export if equal to '')
# show_plot: If the plot should be opened in the browser after running the function
def plot_par2_best(input_file_par2_scores, input_file_bss, plot_description, max_cluster_amount, cutoff, output_file='',
                   show_plot=False):
    data = read_evaluation_json(input_file_par2_scores)
    bss = read_evaluation_json(input_file_bss)
    sorted_data = sorted(data, key=lambda d: d['par2'][0])
    keys = [-1]
    values = [0]
    values_big = [0]
    bss = [bss[0]]
    text = ['Best Single Solver']
    for idx, evaluation in enumerate(sorted_data):
        if len(keys) >= cutoff:
            break

        if len(evaluation['clusters']) > max_cluster_amount:
            values_big.append(evaluation['par2'][0])
            values.append(0)
        else:
            values.append(evaluation['par2'][0])
            values_big.append(0)

        bss.append(0)

        keys.append(idx)
        text.append(str(evaluation['settings']) + ' cluster count: ' + str(len(evaluation['clusters'])))

    fig = go.Figure(layout=go.Layout(
        title=go.layout.Title(text=plot_description + ' of ' + str(cutoff) + ' best evaluations')
    ),
        data=[
            go.Bar(name='Par2 Score <' + str(max_cluster_amount) + ' clusters', x=keys, y=values, hovertext=text),
            go.Bar(name='Par2 Score >' + str(max_cluster_amount) + ' clusters', x=keys, y=values_big, hovertext=text),
            go.Bar(name='Best single solver', x=keys, y=bss, hovertext=text)
        ])

    fig.update_layout(barmode='stack')
    fig.update_xaxes(title_text='Instances sorted by best par2 score')
    fig.update_yaxes(title_text='par2 score')

    if output_file != '':
        exportFigure.export_plot_as_html(fig, output_file)

    if show_plot:
        fig.show()


# Example:

# plot_par2_best('par2', 'bss', 'Par 2 scores', 50, 150, show_plot=True)


# ----------------------------------------------------------------------------------------------------------------------

# Draws a plot of the mean par2 score and the par2 score of the clusters as blobs (with respective size to the
# amount of instances in the cluster
# input_file: The file to read the par2 scores from
# plot_description: The title/description of the plot
# settings_dict: The settings of the clustering we want to plot (for how the dict should look, see the comment on
# the collect_evaluation function
# iter_param: The parameter to iterate on the x axis (must be sortable)
# iter_param_label: The label of the x axis
# output_file: The filename of the exported html (no export if equal to '')
# show_plot: If the plot should be opened in the browser after running the function
# show_best_solver: If the best solver should be written above each cluster blob (without hovering)
def plot_par2(input_file, plot_description, settings_dict, iter_param, iter_param_label, output_file='',
              show_plot=False,
              show_best_solver=False):
    data, diff = collect_evaluation(input_file, settings_dict)
    if iter_param not in diff:
        raise AssertionError('Iteration Parameter not in selected evaluations')

    sorted_data = sorted(data, key=lambda d: d['settings'][iter_param])

    p_keys_par2 = []
    p_value_par2 = []
    p_keys_amount = []
    p_value_amount = []
    p_size_amount = []
    p_text_amount = []
    for evaluation in sorted_data:
        iter_value = evaluation['settings'][iter_param]
        p_keys_par2.append(iter_value)
        p_value_par2.append(evaluation['par2'][0])
        p_keys_amount = p_keys_amount + [iter_value] * len(evaluation['clusters'])
        p_value_amount = p_value_amount + [evaluation['par2'][1][str(cluster)][-1] for cluster in
                                           evaluation['clusters']]
        cluster_size = Counter(evaluation['clustering'])
        p_size_amount = p_size_amount + [cluster_size[cluster] for cluster in evaluation['clusters']]
        p_text_amount = p_text_amount + [evaluation['par2'][1][str(cluster)][0][0:5] for cluster in
                                         evaluation['clusters']]

    fig = go.Figure(layout=go.Layout(
        title=go.layout.Title(text=plot_description)
    ))

    mode = 'markers'
    if show_best_solver:
        mode = 'markers+text'

    fig.add_trace(go.Scatter(x=list(p_keys_par2), y=p_value_par2, mode='lines', name='Mean par2 score'))
    fig.add_trace(go.Scatter(x=p_keys_amount, y=p_value_amount, mode=mode,
                             marker=dict(size=[np.sqrt(item / np.pi) * 2 for item in p_size_amount]),
                             text=[elem[0][0] for elem in p_text_amount], name='Par2 score per cluster',
                             hovertext=p_text_amount, textposition='top center'))

    fig.update_xaxes(title_text=iter_param_label)
    fig.update_yaxes(title_text='par2 score')

    if output_file != '':
        exportFigure.export_plot_as_html(fig, output_file)

    if show_plot:
        fig.show()


# Examples

# plot_par2('par2', 'Par2 scores for each k in [1,9] with kmeans using base.db.',
#           {"scaling_algorithm": ["SCALEMINUSPLUS1"], "scaling_technique": ["NORMALSCALE"],
#            "selection_algorithm": ["NONE"],
#            "selected_data": [["base"]], "cluster_algorithm": ["KMEANS"], "seed": [0]}, "n_clusters_k_means", 'k',
#           show_plot=True)
#
# plot_par2('par2', 'Par2 scores for each eps with dbscan using base.db.',
#           {"scaling_algorithm": ["SCALEMINUSPLUS1"], "scaling_technique": ["NORMALSCALE"],
#            "selection_algorithm": ["NONE"],
#            "selected_data": [["base"]], "cluster_algorithm": ["DBSCAN"], 'min_samples_dbscan': [3]},
#            "eps_dbscan", 'eps',
#           show_plot=True)

# ----------------------------------------------------------------------------------------------------------------------


def plot_mutual_info(input_file, plot_description, settings_dict, iter_param, iter_param_label, mutual_info_param,
                     mutual_info_label, output_file='',
                     show_plot=False):
    data, diff = collect_evaluation(input_file, settings_dict)
    if iter_param not in diff:
        raise AssertionError('Iteration Parameter not in selected evaluations')

    combinations = settings_dict['selected_data']

    fig = go.Figure(layout=go.Layout(
        title=go.layout.Title(text=plot_description)
    ))
    fig.update_xaxes(title_text=iter_param_label)
    fig.update_yaxes(title_text=mutual_info_label)

    for comb in combinations:
        comb_data = []
        for evaluation in data:
            if evaluation['settings']['selected_data'] == comb:
                comb_data.append(evaluation)

        comb_data = sorted(comb_data, key=lambda d: d['settings'][iter_param])
        keys = []
        value = []
        for evaluation in comb_data:
            keys.append(evaluation['settings'][iter_param])
            value.append(evaluation[mutual_info_param])

        fig.add_trace(go.Scatter(x=keys, y=value, mode='lines', name=" ".join(str(x) for x in comb)))

    if output_file != '':
        exportFigure.export_plot_as_html(fig, output_file)

    if show_plot:
        fig.show()


plot_mutual_info('normalized_mututal_information_family',
                 'Normalized mutual information between clustering and the cluster induced by the families',
                 {"scaling_algorithm": ["SCALEMINUSPLUS1"], "scaling_technique": ["NORMALSCALE"],
                  "selection_algorithm": ["NONE"],
                  "selected_data": [["base"], ['gate'], ['solver'], ['base', 'gate'], ['base', 'solver'], ['gate', 'solver'],
                                    ['base', 'gate', 'solver']],
                  "cluster_algorithm": ["KMEANS"], "seed": [0]}, "n_clusters_k_means", 'k',
                 'normalized_mutual_information_family', 'Normalized Mutual Information',
                 show_plot=True
                 )
