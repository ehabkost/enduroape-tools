import unittest, sys
from enduroape.trilhape.planilha import CircuitoState

import logging
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class TesteParciais(unittest.TestCase):
    def assertList(self, passos, l):
        r = list(CircuitoState.posicoes_parciais(passos))
        self.assertEquals(r, l)

    def testSimple(self):
        al = self.assertList

        al(3, [])
        al(5, [])
        al(7, [])

        al(10, [5])
        al(12, [5])
        al(14, [5, 10])

        al(20, [5, 15])
        al(30, [5, 10, 20, 25])
        al(32, [5, 10, 20, 25])
        al(34, [5, 10, 20, 30])

        al(35, [5, 10, 20, 30])

        al(100, [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95])
        al(98, [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95])
        al(104, [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])


if __name__ == '__main__':
    unittest.main()
