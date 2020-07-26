import toy
import toy.app
from nonoverlap import Game

def main():
    game = Game()
    app = toy.app.App(game)
    app.run()

if __name__ == '__main__':
    main()
