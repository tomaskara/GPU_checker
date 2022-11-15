from django.shortcuts import render
from django.http import HttpResponse
from pridani.models import Gpu
from .forms import GputypeForm
from .scrapers import alza, softcomp, czc, alza_s, tsbohemia_api
from datetime import datetime
import subprocess


def zaplnenost():
    result = len(Gpu.objects.all())
    if result > 9000:
        del_gpus = Gpu.objects.all().order_by("date")[:result-9000]
        lenght_for_del = len(del_gpus)
        for i in del_gpus:
            i.delete()
        return
    else:
        return



def index(request):
    volba = request.GET.get('m', 'Vše')
    """form = GputypeForm(initial={'Model': 'Vše'})
    volba = request.POST.get("Model", "Vše")
    form = GputypeForm(initial={'Model': volba})"""
    if volba == "Vše":
        gpus = Gpu.objects.all().filter(stock=True).order_by("price")
    else:
        gpus = Gpu.objects.filter(version=volba).filter(stock=True).order_by("price")
    return render(request, "pridani/vypis.html", {
        "gpus": gpus,
        "volba": volba
    })





def filtrace(request):
    form = GputypeForm(initial={'Model': 'Vše'})
    volba = request.POST.get("Model", "Vše")
    form = GputypeForm(initial={'Model': volba})
    if volba == "Vše":
        gpus = Gpu.objects.all().order_by("price")
    else:
        gpus = Gpu.objects.filter(version=volba)
    return render(request, "pridani/filtrace.html", {
        "form": form,
        "gpus": gpus,
        "volba": volba,
    })

def pridavam(request):
    return HttpResponse(alza()+czc()+softcomp())

def pridavamts(request):
    return HttpResponse(tsbohemia_api())


def vypis(request):
    gpus = Gpu.objects.all().filter(stock=True).order_by("price")
    return render(request, "pridani/vypis.html", {
        "gpus": gpus,
    })


def vymazat(request):
    Gpu.objects.all().delete()
    return HttpResponse("Vymazáno")

def graph(request):
    name = request.GET.get('n', '')
    shop = request.GET.get('s', '')
    filtered_data = Gpu.objects.filter(name=name).filter(shop=shop).order_by("date")
    labels = []
    data = []
    for i in filtered_data:
        dt = i.date
        labels.append(str(dt.day)+"."+str(dt.month)+"."+str(dt.year))
        data.append(i.price)
    return render(request, "pridani/graph.html", {
        "labels": labels,
        "data": data
    })
