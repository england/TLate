import sublime, sublime_plugin
import urllib
import json
import re

global tlate_awaiting

class HuehueCommand(sublime_plugin.TextCommand):
  def run(self, edit, *args):
    print('second level command fired')

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
    self.sel = self.window.active_view().sel()[0]
    sublime.set_timeout_async(self.__call_remote_service, 0)

  def __call_remote_service(self):
    text = self.window.active_view().substr(self.sel)
    lang = self.__detect_lang(text)
    params = {
      "client": 'x',
      "text": text,
      "sl": lang,
      "tl": self.DIRECTIONS[lang]
    }
    params = urllib.parse.urlencode(params)
    page = self.OPENER.open("http://translate.google.ru/translate_a/t?" + params)
    self.result = json.loads(page.read().decode('utf-8'))
    self.__show_translations_panel()

  def __detect_lang(self, text):
    if len(self.RU.findall(text)) > len(self.EN.findall(text)):
      return("ru")
    else:
      return("en")

  def __show_translations_panel(self):
    global tlate_awaiting
    tlate_awaiting = 'tlate_translations_panel'
    self.window.show_quick_panel(self.__translation_panel_items(),
                                 self.__replace_selections,
                                 0,
                                 0,
                                 self.__on_highlighted)

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
      view.run_command("replace_selection_with_translation",
        { "a": self.sel.a, "b": self.sel.b, "translation": translation })
    view.settings().set('tlate_translations_panel_activated', False)

  def __on_highlighted(self, idx):
    print('on highlighted: ', idx)

class ReplaceSelectionWithTranslation(sublime_plugin.TextCommand):
  def run(self, edit, **args):
    self.view.replace(edit, sublime.Region(args['a'], args['b']), args['translation'])

class Werqwedq(sublime_plugin.EventListener):
  def on_activated_async(self, view):
    global tlate_awaiting
    views_ids = [v.view_id for v in view.window().views()]
    if tlate_awaiting == 'tlate_translations_panel' and view.view_id not in views_ids:
      view.settings().set('tlate_translations_panel_activated', True)
      tlate_awaiting = None

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
