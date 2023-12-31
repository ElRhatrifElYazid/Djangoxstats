import os
from django.conf import settings
from django.shortcuts import render, redirect, HttpResponse
import pandas as pd  # Note the corrected import statement
import requests
from .forms import BinomialForm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO, BytesIO
import base64
from .forms import FileUploadForm,ExponentielleForm,TraitementForm,UniformeForm,PoissonForm,NormaleForm 
import json
import plotly.express as px
import matplotlib
import plotly.graph_objs as go
from scipy.stats import binom
from django.http import JsonResponse
import plotly.io as pio
from .forms import BernoulliForm 
from scipy.stats import bernoulli
matplotlib.use('Agg')

import plotly.figure_factory as ff


def index(request):
    return render(request, 'index.html')

def generate_chart(df, type_chart, col1, col2):
    buffer = BytesIO()

    if type_chart == 'Barplot':
        fig = px.bar(df, x=col1, y=col2)
        fig.update_layout(xaxis_title=col1, yaxis_title=col2, title='Bar Plot')
        return fig.to_json()

    elif type_chart == 'histogram':
        fig = px.histogram(df, x=col1)
        fig.update_layout(xaxis_title=col1, yaxis_title='Count', title='Histogram', barmode='overlay', bargap=0.1)
        return fig.to_json()

    elif type_chart == 'piechart':
        value_counts = df[col1].value_counts().reset_index()
        value_counts.columns = [col1, 'Count']
        fig = px.pie(value_counts, values='Count', names=col1, title='Pie Chart')
        return fig.to_json()


    elif type_chart == 'scatterplot':
        fig = px.scatter(df, x=col1, y=col2)
        fig.update_layout(xaxis_title=col1, yaxis_title=col2, title='Scatter Plot')
        return fig.to_json()

    elif type_chart == 'heatmap':
        df_encoded = df.copy()
        for column in df_encoded.columns:
            if df_encoded[column].dtype == 'object':
                df_encoded[column], _ = pd.factorize(df_encoded[column])
        fig = px.imshow(df_encoded.corr(), color_continuous_scale='Viridis')
        fig.update_layout(title='Heatmap')
        return fig.to_json()

    elif type_chart == 'lineplot':
       
        fig = px.line(df, x=col1, y=col2,markers=True)
        fig.update_layout(xaxis_title=col1, yaxis_title=col2, title='Line Plot')
        return fig.to_json()

        
    elif type_chart == 'boxplot':
        fig = px.box(df, x=col1)
        fig.update_layout(title='Box Plot')
        return fig.to_json()
        

    elif type_chart == 'violinplot':
        fig = px.violin(df, y=col1, box=True)
        fig.update_layout(yaxis_title=col1, title='Violin Plot')
        return fig.to_json()

    elif type_chart == 'kdeplot':
        data_to_plot = df[col1].replace([np.inf, -np.inf], np.nan).dropna()

        group_labels = ['distplot']
        fig = ff.create_distplot([data_to_plot], group_labels, curve_type='kde')

        
        fig.update_layout(
            title="Kernel Density Estimation (KDE) Plot",
            yaxis_title="Density",
            xaxis_title=col1,
            showlegend=False
        )

        fig_json = fig.to_json()

        return fig_json

def excel(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            fichier = request.FILES['file']

            if fichier.name.endswith(('.xls', '.xlsx')):
                try:
                    data = pd.read_excel(fichier)
                    df = pd.DataFrame(data)
                    columns_choices = [(col, col) for col in df.columns]
                    df_json = df.to_json()
                    request.session['df_json']=df_json
                    return render(
                        request,
                        'visualiser_data.html',
                        {'form': form,  'df': df.to_html(classes='table table-bordered'), 'column_names': df.columns},
                    )
                except pd.errors.ParserError as e:
                    e = f"Erreur : Impossible de lire le fichier Excel. Assurez-vous que le fichier est au format Excel valide."
                    return render(request, 'excel.html', {'form': form, 'error_message': e})
            else:
                return HttpResponse("Seuls les fichiers Excel (.xls, .xlsx) sont autorisés. Veuillez télécharger un fichier Excel.")
    else:
        form = FileUploadForm()

    return render(request, 'excel.html', {'form': form})

def visualiser(request): 
    return render(request, 'visualiser_data.html')

def visualiser_chart(request): 
    if request.method == 'POST':
        col1 = request.POST['col_name1']
        col2 = request.POST['col_name2']
        type_chart = request.POST['type_chart']
        df_json = request.session.get('df_json')
        
        df_json_io = StringIO(df_json)
        df = pd.read_json(df_json_io)
       
        if pd.api.types.is_string_dtype(df[col1]) and type_chart in ['kdeplot', 'violinplot', 'boxplot']:
            error_message = "La colonne choisie est de type 'string', veuillez choisir une autre colonne."
            return render(request, 'diagramme.html', {'error_message': error_message})
        elif type_chart=="Nothing":
            error_message = "Veuillez sélectionner un diagramme à afficher"
            return render(request, 'diagramme.html', {'error_message': error_message})
        
        chart = generate_chart(df, type_chart, col1, col2)
        return render(request, 'diagramme.html', {'chart': chart})
    
    return render(request, 'visualiser_data.html')

def diagramme(request):
    return render(request, 'diagramme.html')

def text(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            fichier = request.FILES['file']
            
           
            if fichier.name.endswith('.txt'):
              
                data = pd.read_csv(fichier)

                df = pd.DataFrame(data)
                columns_choices = [(col, col) for col in df.columns]
                df_json = df.to_json()
                request.session['df_json'] = df_json
                return render(
                        request,
                        'visualiser_data.html',
                        {'form': form,  'df': df.to_html(classes='table table-bordered'), 'column_names': df.columns},
                )    
            else:
                return HttpResponse("Seuls les fichiers text sont autorisés. Veuillez télécharger un fichier txt.")
    else:
        form = FileUploadForm()

    return render(request, 'text.html', {'form': form})

def csv(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            fichier = request.FILES['file']
            if fichier.name.endswith('.csv'):
                # Traitez le fichier CSV
                data = pd.read_csv(fichier)
                df = pd.DataFrame(data)
                columns_choices = [(col, col) for col in df.columns]
                df_json = df.to_json()
                request.session['df_json'] = df_json

                return render(
                        request,
                        'visualiser_data.html',
                        {'form': form,  'df': df.to_html(classes='table table-bordered'), 'column_names': df.columns},
                )
            else:
                return HttpResponse("Seuls les fichiers CSV sont autorisés. Veuillez télécharger un fichier CSV.")
    else:
        form = FileUploadForm()

    return render(request, 'csv.html', {'form': form})


def parcourir_chart(request):
    df = None
    columns_choices = None
    error_message = ""
    max_row = 0

    if 'df_json' in request.session:
        df_json = request.session['df_json']
        df = pd.read_json(StringIO(df_json))
        columns_choices = [col for col in df.columns]
        max_row = df.shape[0] - 1
        
    if request.method == 'POST':
        selected_columns = request.POST.getlist('selected_columns')
        parcourir_chart_type = request.POST.get('parcourir_chart')
        col_name1 = request.POST.get('col_name1')
        row_numb = request.POST.get('RowNumb')
        
        if selected_columns:
            df = df[selected_columns]

        
        if parcourir_chart_type == 'FindElem' and df is not None:
            try:
                row_numb = int(row_numb)
                row_numb = min(row_numb, max_row)
                resultats_recherche = df.at[row_numb, col_name1]
                contexte = {'resultat': resultats_recherche, 'column_names': columns_choices, 'df': df.to_html(classes='table table-bordered'), 'max_row': max_row}
                return render(request, 'parcourir.html', contexte)
            except (ValueError, KeyError, IndexError):
                pass

        parcourir_rows_type = request.POST.get('parcourir_rows')

        if parcourir_rows_type == 'NbrOfRowsTop':
            nb_rows_top = int(request.POST.get('Head'))
            df = df.head(nb_rows_top)
        elif parcourir_rows_type == 'NbrOfRowsBottom':
            nb_rows_bottom = int(request.POST.get('Tail'))
            df = df.tail(nb_rows_bottom)
        elif parcourir_rows_type == 'FromRowToRow':
            from_row = int(request.POST.get('FromRowNumb'))
            to_row = int(request.POST.get('ToRowNumb'))
            df = df.loc[from_row:to_row]

    contexte = {
        'df': df.to_html(classes='table table-bordered') if df is not None else None,
        'column_names': columns_choices,  # Utilisez columns_choices ici pour les autres actions
        'max_row': max_row
    }   
    return render(request, 'parcourir.html', contexte)

#//////////////////////////////// LOIS ////////////////////////////////////////////////////////////////
def Binomiale(request):
    if request.method == 'POST':
        form = BinomialForm(request.POST)
        if form.is_valid():
            n = form.cleaned_data['n']
            p = form.cleaned_data['p']

            data_binomial = binom.rvs(n=n, p=p, loc=0, size=1000)
            fig = px.histogram(x=data_binomial, nbins=n+1, title='Distribution Binomiale')
            fig.update_layout(xaxis_title='Binomial', yaxis_title='Fréquence relative',bargap=0.2)
            plot_data = fig.to_json()

            return render(request, 'binomiale.html', {'form': form, 'plot_data': plot_data})
    else:
        form = BinomialForm()

    return render(request, 'binomiale.html', {'form': form})


def Bernoulli(request):
    if request.method == 'POST':
        form = BernoulliForm(request.POST)
        if form.is_valid():
            p = form.cleaned_data['p']
            data_bernoulli = bernoulli.rvs(p, size=1000)
            fig = px.histogram(x=data_bernoulli, nbins=2, title='Distribution de Bernoulli')
            fig.update_layout(xaxis_title='Bernoulli', yaxis_title='Fréquence relative',bargap=0.2)
            plot_data = fig.to_json()

            return render(request, 'bernoulli.html', {'form': form, 'plot_data': plot_data})
    else:
        form = BernoulliForm()

    return render(request, 'bernoulli.html', {'form': form})

def Normale(request):
    if request.method == 'POST':
        form = NormaleForm(request.POST)
        if form.is_valid():
            mean = form.cleaned_data['mean']
            std_dev = form.cleaned_data['std_dev']
            data_normale = np.random.normal(mean, std_dev, size=1000)
            fig = px.histogram(x=data_normale, title='Distribution Normale Continue')
            fig.update_layout(xaxis_title='Valeur', yaxis_title='Fréquence relative',bargap=0.2)

            # Convertir la figure en JSON
            plot_data = fig.to_json()

            return render(request, 'normale.html', {'form': form, 'plot_data': plot_data})
    else:
        form = NormaleForm()

    return render(request, 'normale.html', {'form': form})



def Poisson(request):
    if request.method == 'POST':
        form = PoissonForm(request.POST)
        if form.is_valid():
            lambda_param = form.cleaned_data['lambda_param']
            data_poisson = np.random.poisson(lambda_param, size=1000)
            fig = px.histogram(x=data_poisson, title='Distribution de Poisson')
            fig.update_layout(xaxis_title='Valeur', yaxis_title='Fréquence relative',bargap=0.2)
            plot_data = fig.to_json()

            return render(request, 'poisson.html', {'form': form, 'plot_data': plot_data})
    else:
        form = PoissonForm()

    return render(request, 'poisson.html', {'form': form})



def Uniforme(request):
    if request.method == 'POST':
        form = UniformeForm(request.POST)
        if form.is_valid():
            a = form.cleaned_data['a']
            b = form.cleaned_data['b']
            data_uniforme = np.random.uniform(a, b, size=1000)
            fig = px.histogram(x=data_uniforme, title='Distribution Uniforme')
            fig.update_layout(xaxis_title='Valeur', yaxis_title='Fréquence relative',bargap=0.2)

            # Convertir la figure en JSON
            plot_data = fig.to_json()

            return render(request, 'uniforme.html', {'form': form, 'plot_data': plot_data})
    else:
        form = UniformeForm()

    return render(request, 'uniforme.html', {'form': form})



def Exponentielle(request):
    if request.method == 'POST':
        form = ExponentielleForm(request.POST)
        if form.is_valid():
            beta = form.cleaned_data['beta']

            # Générer des échantillons de la distribution exponentielle
            data_exponentielle = np.random.exponential(scale=beta, size=1000)

            # Créer un histogramme interactif avec Plotly Express
            fig = px.histogram(x=data_exponentielle, title='Distribution Exponentielle')
            fig.update_layout(xaxis_title='Valeur', yaxis_title='Fréquence relative',bargap=0.2)

            # Convertir la figure en JSON
            plot_data = fig.to_json()

            return render(request, 'exponentielle.html', {'form': form, 'plot_data': plot_data})
    else:
        form = ExponentielleForm()

    return render(request, 'exponentielle.html', {'form': form})




