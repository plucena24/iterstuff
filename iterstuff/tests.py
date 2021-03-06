#!/usr/bin/env python
import string
from unittest import TestCase, main

from recipes import batch, repeatable_takewhile, chunked
from lookahead import Lookahead


class LookaheadTest(TestCase):

    def test_lookahead(self):
        l = Lookahead([])
        self.assertTrue(l.atstart)
        self.assertTrue(l.atend)
        self.assertIsNone(l.peek)
        self.assertEqual(len(list(l)), 0)

        l = Lookahead("a")
        self.assertTrue(l.atstart)
        self.assertFalse(l.atend)
        self.assertEqual(l.peek, 'a')
        self.assertEqual(l.next(), 'a')
        self.assertFalse(l.atstart)
        self.assertTrue(l.atend)
        self.assertRaises(StopIteration, l.next)

        l = Lookahead(range(10))
        self.assertTrue(l.atstart)
        self.assertFalse(l.atend)
        self.assertEqual(l.peek, 0)
        self.assertEqual(l.next(), 0)
        self.assertEqual(l.next(), 1)
        self.assertEqual(l.peek, 2)
        self.assertFalse(l.atstart)
        self.assertFalse(l.atend)
        self.assertEqual(list(l), [2, 3, 4, 5, 6, 7, 8, 9])
        self.assertTrue(l.atend)


class RecipeTests(TestCase):

    def test_repeatable_takewhile(self):
        data = Lookahead(x for x in 'abcd123ghi')

        self.assertEqual(
            list(
                repeatable_takewhile(
                    lambda x: not x.isdigit(),
                    data
                )
            ),
            list('abcd')
        )

        self.assertEqual(
            list(
                repeatable_takewhile(
                    lambda x: x.isdigit(),
                    data
                )
            ),
            list('123')
        )

        self.assertEqual(list(data), list('ghi'))

    def test_chunked(self):
        r = map(list, chunked(""))
        self.assertEqual(len(r), 0)

        r = map(list, chunked("a"))
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][0], 'a')
        self.assertEqual(len(r[0]), 1)

        r = map(list, chunked("aA", string.lower))
        self.assertEqual(len(r), 1)
        r2 = r[0]
        self.assertEqual(len(r2), 2)
        self.assertEqual(r2, ['a', 'A'])

        r = map(list, chunked("ab"))
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0], ['a'])
        self.assertEqual(r[1], ['b'])

        r = map(list, chunked("aabcc"))
        self.assertEqual(len(r), 3)
        self.assertEqual(r[0], list("aa"))
        self.assertEqual(r[1], list("b"))
        self.assertEqual(r[2], list("cc"))

        r = map(list, chunked("abBbb", string.lower))
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0], ['a'])
        self.assertEqual(r[1], list("bBbb"))

        r = map(list, chunked("abBbbC", string.lower))
        self.assertEqual(len(r), 3)
        self.assertEqual(r[0], ['a'])
        self.assertEqual(r[1], list("bBbb"))
        self.assertEqual(r[2], ['C'])

    def test_batching(self):
        seq = xrange(19)
        previous_list = None
        for batchiter in batch(seq, 3):
            x = list(batchiter)
            self.assertEqual(len(x),
                             1 if x[0]==18 else 3)
            if previous_list is None:
                self.assertEqual(x[0], 0)
            else:
                self.assertEqual(x[0], previous_list[-1]+1)
            previous_list = x

if __name__ == '__main__':
    main()
