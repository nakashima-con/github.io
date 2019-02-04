from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from slacker import Slacker

import datetime
import os, sys

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)

from .models import *
from . import forms
import config

CHANNEL_ID = 'G8XP0KUNQ'

class Slack(object):
  __slacker = None

  def __init__(self, token):
    self.__slacker = Slacker(token)

  def post_to_channel(self, channel, message):
    self.__slacker.chat.post_message(CHANNEL_ID, message)

slack = Slack(config.slack_token)

def index(request):
  equipment_list = Equipment.objects.all()
  context = {
    'equipment_list': equipment_list,
  }
  return render(request, 'equipments/index.html', context)

def detail(request, equipment_id):
  equipment = get_object_or_404(Equipment, pk=equipment_id)
  form = forms.BorrowForm()

  context = {
    'equipment': equipment,
    'form': form,
  }
  return render(request, 'equipments/detail.html', context)

def act(request, equipment_id):
  temp = Equipment.objects.get(pk=equipment_id)

  if request.POST['action'] == 'borrowing':
    if temp.state == 0:
      dueday = datetime.date.today() + datetime.timedelta(days=13)

      temp.borrower = request.POST['name']
      temp.state = 1
      temp.due = dueday
      temp.save()

      pm = temp.borrower + "が" + temp.name + "を貸出しました。返却期限は" + str(temp.due) + "です。"
      slack.post_to_channel('bot_test', pm)

    return HttpResponseRedirect(reverse('equipments:index'))

  if request.POST['action'] == 'returning':
    if temp.borrower == request.POST['name']:

      pm = temp.borrower + "が" + temp.name + "を返却しました。"
      slack.post_to_channel('bot_test', pm)
       
      temp.borrower = ""
      temp.state = 0
      temp.save()

    return HttpResponseRedirect(reverse('equipments:index'))

  if request.POST['action'] == 'extension':
    if temp.borrower == request.POST['name']:
      if temp.due < datetime.date.today():
        dueday = datetime.date.today() + datetime.timedelta(days=7)
      else:
        dueday = temp.due + datetime.timedelta(days=7)
      temp.due = dueday
      temp.save()

      pm = temp.borrower + "が" + temp.name + "の貸出を延長しました。返却期限は" + str(temp.due) + "です。"
      slack.post_to_channel('bot_test', pm)

    return HttpResponseRedirect(reverse('equipments:index'))
  return HttpResponseRedirect(reverse('equipments:index'))

def new(request):
  form = forms.NewForm()

  context = {
    'form': form,
  }

  return render(request, 'equipments/new.html', context)

def create(request):
  temp = Equipment(
    name=request.POST['name'], 
    eq_type=request.POST['eq_type'], 
    state=0,
    owner='',
    due=datetime.date.today(), 
    remark=request.POST['remark']
    )
  temp.save()

  return HttpResponseRedirect(reverse('equipments:index'))
