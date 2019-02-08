import requests
import json

class BotClient:
  def __init__(self):
    self. endpoint = \
      'http://localhost:8080/'

  def get_po_status(self, po_number):
    url = self.endpoint + "poStatus"
    data = {"po_number":po_number}
    headers={
      "Accept": "application/json",
      'content-type': 'application/json'
    }
    return requests.post(url, data=json.dumps(data), headers=headers).json()

  def get_pr_approver(self, pr_number):
    url = self.endpoint + "prApprover"
    data = {"pr_number":pr_number}
    headers={
      "Accept": "application/json",
      'content-type': 'application/json'
    }
    return requests.post(url, data=json.dumps(data), headers=headers).json()

  def check_vendor_availability(self, system, supplier, countries):
    url = self.endpoint + "vendorAvailability"
    data = {"system":system,"supplier":supplier,"countries":countries}
    headers={
      "Accept": "application/json",
      'content-type': 'application/json'
    }
    return requests.post(url, data=str(data), headers=headers).json()


def main():
  obj = BotClient()
  print(obj.get_pr_approver("pr8687"))

if __name__ == '__main__':
    main()