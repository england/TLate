import sublime, sublime_plugin
import urllib
import json
import re

# first level quick panel items
global translation_panel_items

# first level quick panel selected item index
global selected_translation_panel_item_idx

# view where translations panel fired
global text_view

class HuehueCommand(sublime_plugin.WindowCommand):
  def run(self):
    print('second level command fired')
    self.window.run_command('hide_overlay')
    # TLateSession().get('translation_panel_items')
    items = translation_panel_items[selected_translation_panel_item_idx][1].split(', ')
    self.window.show_quick_panel(items,
                                 self.__replace_selections,
                                 0,
                                 0,
                                 None)

  def __sel(self):
    return self.window.active_view().sel()[0]

  def __replace_selections(self, idx):
    replacer = translation_panel_items[selected_translation_panel_item_idx][1].split(', ')[idx]
    self.window.active_view().run_command("tlate_replace_selection",
      { "a": self.__sel().a, "b": self.__sel().b, "replacer": replacer })

class TlateTranslationsCommand(sublime_plugin.WindowCommand):
  class GoogleCompatibleOpener(urllib.request.FancyURLopener):
    # some random user-agent
    version = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.114 Safari/537.36'

  OPENER = GoogleCompatibleOpener()

  TYPES = ["sentences"]
  DIRECTIONS = { "ru": "en", "en": "ru" }
  EN = re.compile("[a-z]", re.IGNORECASE)
  RU = re.compile("[а-я]", re.IGNORECASE)

  def run(self):
    global text_view
    text_view = self.window.active_view()
    sublime.set_timeout_async(self.__call_remote_service, 0)

  def __sel(self):
    return self.window.active_view().sel()[0]

  def __call_remote_service(self):
    text = self.window.active_view().substr(self.__sel())
    lang = self.__detect_lang(text)
    params = {
      "client": 'x',
      "text": text,
      "sl": lang,
      "tl": self.DIRECTIONS[lang]
    }
    params = urllib.parse.urlencode(params)
    self.window.active_view().set_status('tlate', 'tlate processing')
    page = self.OPENER.open("http://translate.google.ru/translate_a/t?" + params)
    self.result = json.loads(page.read().decode('utf-8'))
    self.__show_translations_panel()
    self.window.active_view().erase_status('tlate')

  def __detect_lang(self, text):
    if len(self.RU.findall(text)) > len(self.EN.findall(text)):
      return("ru")
    else:
      return("en")

  def __show_translations_panel(self):
    global translation_panel_items
    translation_panel_items = self.__translation_panel_items()
    show_and_wait_quick_panel('tlate_translations_panel', lambda: self.window.show_quick_panel(translation_panel_items, self.__replace_selections, 0, 0, self.__on_highlighted))
    # TLateSession().panel_expected('tlate_translations_panel')
    # self.window.show_quick_panel(translation_panel_items, self.__replace_selections, 0, 0, self.__on_highlighted)

  def __translation_panel_items(self):
    translations = []
    if 'dict' in self.result:
      for part_of_speech in self.result['dict']:
        for entry in part_of_speech['entry']:
          translations.append([
            entry['word'],
            ', '.join(entry['reverse_translation']),
            part_of_speech['pos']
          ])
    else:
      translations = [[self.result['sentences'][0]['trans'], '-', '-']]
    return translations

  def __replace_selections(self, idx):
    view = self.window.active_view()
    if idx != -1:
      translation = self.__translation_panel_items()[idx][0]
      view.run_command("tlate_replace_selection",
        { "a": self.__sel().a, "b": self.__sel().b, "replacer": translation })
    view.settings().set('tlate_translations_panel_activated', False)

  def __on_highlighted(self, idx):
    print('on highlighted: ', idx)
    global selected_translation_panel_item_idx
    selected_translation_panel_item_idx = idx

class TlateReplaceSelection(sublime_plugin.TextCommand):
  def run(self, edit, **args):
    self.view.replace(edit, sublime.Region(args['a'], args['b']), args['replacer'])

class Werqwedq(sublime_plugin.EventListener):
  def on_activated_async(self, view):
    if view_is_expected_panel(view, 'tlate_translations_panel'):
      view.settings().set('tlate_translations_panel_activated', True)

def show_and_wait_quick_panel(name, func):
    TLateSession().panel_expected(name)
    func()

def view_is_expected_panel(view, name):
  return view_is_quick_panel(view) and TLateSession().is_panel_expected(name)

def view_is_quick_panel(view):
  return view.view_id not in [v.view_id for v in view.window().views()]

class TLateSession(object):
  def __new__(klass):
    if not hasattr(klass, 'instance'):
      klass.instance = super(TLateSession, klass).__new__(klass)
      klass.name = None
    return klass.instance

  def panel_expected(self, name):
    self.name = name

  def is_panel_expected(self, name):
    if self.name == name:
      self.name = None
      return True
    else:
      return False

  def set(self, name, value):
    pass

  def get(self, name):
    pass

# TLateSession().wait('asd')

# response examples:
#   phrase:
#     {
#       "sentences":[
#         {
#           "trans":"выполняются в отдельном потоке",
#           "orig":"run in separate thread",
#           "translit":"vypolnyayutsya v otdel'nom potoke",
#           "src_translit":""
#         }
#       ],
#       "src":"en",
#       "server_time":1
#     }

#   single word:
#     {
#       "sentences":[
#         {
#           "trans":"результат",
#           "orig":"result",
#           "translit":"rezul'tat",
#           "src_translit":""
#         }
#       ],
#       "dict":[
#         {
#           "pos":"имя существительное",
#           "terms":[
#             "результат",
#             "следствие",
#             "исход",
#             "эффект",
#             "итог",
#             "результат вычисления"
#           ],
#           "entry":[
#             {
#               "word":"результат",
#               "reverse_translation":[
#                 "result",
#                 "outcome",
#                 "output",
#                 "effect",
#                 "product",
#                 "fruit"
#               ],
#               "score":0.687289298
#             },
#             {
#               "word":"следствие",
#               "reverse_translation":[
#                 "consequence",
#                 "investigation",
#                 "result",
#                 "effect",
#                 "consequent",
#                 "inquiry"
#               ],
#               "score":0.00113485544
#             },
#             { ... },
#             { ... },
#             {
#               "word":"результат вычисления",
#               "reverse_translation":[
#                 "result"
#               ],
#               "score":6.04895513e-06
#             }
#           ],
#           "base_form":"result",
#           "pos_enum":1
#         },
#         {
#           "pos":"глагол",
#           "terms":[
#             "следовать",
#             "иметь результатом",
#             "проистекать",
#             "кончаться",
#             "происходить в результате"
#           ],
#           "entry":[
#             {
#               "word":"следовать",
#               "reverse_translation":[
#                 "follow",
#                 "abide by",
#                 "result",
#                 "steer",
#                 "ensue",
#                 "behoove"
#               ],
#               "score":0.00148013048
#             },
#             {
#               "word":"иметь результатом",
#               "reverse_translation":[
#                 "result",
#                 "issue"
#               ],
#               "score":0.000732717745
#             },
#             { ... },
#             { ... }
#           ]
#         }
#       ]
#     }
