from kivy.app import App
from kivy.uix.label import Label

class AlmightyRandomApp(App):
    def build(self):
        return Label(text='Almighty Random Works!', font_size='50sp', halign='center')

if __name__ == '__main__':
    AlmightyRandomApp().run()
