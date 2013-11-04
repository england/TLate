import sublime, sublime_plugin
import urllib
import json
import re


class TlateCommand(sublime_plugin.TextCommand):
  class GoogleCompatibleOpener(urllib.request.FancyURLopener):
    # some random user-agent
    version = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.114 Safari/537.36'

  OPENER = GoogleCompatibleOpener()

  TYPES = ["sentences"]
  DIRECTIONS = { "ru": "en", "en": "ru" }
  EN = re.compile("[a-z]", re.IGNORECASE)
  RU = re.compile("[а-я]", re.IGNORECASE)

  def run(self, edit, *args):
    self.edit = edit
    self.sel = self.view.sel()[0]
    sublime.set_timeout_async(self.__call_remote_serice, 0)

  def __call_remote_serice(self):
    text = self.view.substr(self.sel)
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
    self.__show_popup_menu()

  def __detect_lang(self, text):
    if len(self.RU.findall(text)) > len(self.EN.findall(text)):
      return("ru")
    else:
      return("en")

  def __show_popup_menu(self):
    self.view.show_popup_menu(self.__translations(), self.__replace_selections)

  def __translations(self):
    return [x["trans"] for x in self.result["sentences"]]

  def __replace_selections(self, idx):
    if idx != -1:
      translation = self.__translations()[idx]
      self.view.run_command("replace_selection_with_translation",
        { "a": self.sel.a, "b": self.sel.b, "translation": translation })

class ReplaceSelectionWithTranslation(sublime_plugin.TextCommand):
  def run(self, edit, **args):
    self.view.replace(edit, sublime.Region(args['a'], args['b']), args['translation'])



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
