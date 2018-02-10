from django.test import TestCase
from django.http import HttpRequest
import json
from wallet.views import *

class CreateTest(TestCase):
    def test_create(self):
        id = 'createtest'
        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = create(req)
        jsondata = json.loads(res.content.decode())
        addr = jsondata['result']
        print('TestCreate - Addr: %s' % addr)
        self.assertTrue(addr != '')

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = create(req)
        jsondata = json.loads(res.content.decode())
        print('TestCreate - Addr: %s' % jsondata['result'])
        self.assertEqual(addr, jsondata['result'])


class AddressTest(TestCase):
    def test_address(self):
        id = 'addrtest'
        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = address(req)
        jsondata = json.loads(res.content.decode())
        self.assertEqual(jsondata['status'], Status.WALLET_NOT_FOUND.value.status_code)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = create(req)
        jsondata = json.loads(res.content.decode())
        addr = jsondata['result']
        print('TestAddress - Addr: %s' % addr)
        self.assertTrue(addr != '')

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = address(req)
        jsondata = json.loads(res.content.decode())
        print('TestAddress - Addr: %s' % jsondata['result'])
        self.assertEqual(jsondata['result'], addr)

class BalanceTest(TestCase):
    def test_balance(self):
        id = 'balancertest'
        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = balance(req)
        jsondata = json.loads(res.content.decode())
        self.assertEqual(jsondata['status'], Status.WALLET_NOT_FOUND.value.status_code)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        create(req)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = balance(req)
        jsondata = json.loads(res.content.decode())
        bal = float(jsondata['result'])
        self.assertAlmostEqual(bal, 0.0, delta=0.001)

class DeleteTest(TestCase):
    def test_delete(self):
        id = 'deletertest'

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = delete(req)
        jsondata = json.loads(res.content.decode())
        self.assertEqual(jsondata['result'], False)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        create(req)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = delete(req)
        jsondata = json.loads(res.content.decode())
        self.assertEqual(jsondata['result'], True)


class ListTest(TestCase):
    def test_list(self):
        id = 'listtest'

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        create(req)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        res = list(req)
        jsondata = json.loads(res.content.decode())


class TipTest(TestCase):
    def test_tip(self):
        id1 = 'tiptest1'
        id2 = 'tiptest2'

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id1}
        req.POST['data'] = json.dumps(params)
        create(req)

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id2}
        req.POST['data'] = json.dumps(params)
        create(req)

        w1 = Wallet.objects.get(name=id1)

        w1.balance = 100
        w1.save()

        req = HttpRequest()
        req.method = 'POST'
        params = {'from': id1, 'to': id2, 'amount': 13}
        req.POST['data'] = json.dumps(params)
        tip(req)

        w2 = Wallet.objects.get(name=id2)

        self.assertAlmostEqual(float(w2.balance), 13 * 0.9998, delta=0.01)

class WithdrawTest(TestCase):
    def test_withdraw(self):
        id = 'withdrawtest'

        req = HttpRequest()
        req.method = 'POST'
        params = {'id': id}
        req.POST['data'] = json.dumps(params)
        create(req)

        w = Wallet.objects.get(name=id)
        w.balance = 0.5
        w.save()

        req = HttpRequest()
        req.method = 'POST'
        params = {'from': id, 'to': 'SjmsPW4m9azLk63nmt5kJLdY8QJixFowzU', 'amount': 0.1}
        req.POST['data'] = json.dumps(params)
        res = send(req)
        jsondata = json.loads(res.content.decode())
        self.assertAlmostEqual(float(jsondata['result']), 0.1 * (1-0.05/100), delta=0.001)

        w = Wallet.objects.get(name=id)
        self.assertAlmostEqual(float(w.balance), 0.4 - 0.05, delta=0.001)