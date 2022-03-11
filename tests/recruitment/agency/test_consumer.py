from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from recruitment.agency import Consumer
from tests.recruitment.agency import uncloseable


class ConsumerTest(TestCase):

    consumer = Consumer()
    head = 'head'
    tail = 'tail'
    separator = '\n'
    head_and_tail = f'{head}{separator}{tail}'

    @patch('builtins.open')
    def test_can_take_oldest_deadletter_first(self, mock_file):
        Consumer.deadletter_file = __file__
        with uncloseable(StringIO(self.head_and_tail)) as buffer:
            mock_file.return_value = buffer
            result = self.consumer.take_deadletter()
            self.assertTrue(result.successful)
            self.assertEqual(result.value, f'{self.head}{self.separator}')

    def test_can_consume(self):
        with self.assertRaises(NotImplementedError):
            self.consumer.consume()
