"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
try:
    from xml.etree import ElementTree as ET
except ImportError, e:
    from elementtree import ElementTree as ET
from suds.client import Client
import email,re

class NotMultipartError(Exception): pass
class UnknownResponse(Exception): pass
class ServerError(Exception): pass

class JasperClient:
    def __init__(self,url,username,password):
        self.client = Client(url,username=username,password=password)
        print(self.client)

    def list(self,dir=""):
        """ get a list containing report URIs on JasperServer
        optional dir param shows the directory to list in JasperServer
        """
        req = createRequest(
            uriString=dir, 
            wsType="folder", 
            operationName="list")
        res = self.client.service.list(req)
        res = res.encode('utf-8')
        reports = []
        for rd in ET.fromstring(res).findall('resourceDescriptor'):
            if rd.get('wsType') == 'reportUnit':
                report = {}
                report['id'] = rd.get('uriString')
                for infotag in ['label','description']:
                    try:
                        report[infotag] = rd.find(infotag).text
                    except AttributeError, e:
                        report[infotag] = None
                reports.append(report)
        return reports

    def get(self, uri):
        ''' Return a list containing Report's parameters:
        report:
            - name
            - id (uriString)
            - label
            - description
            - controls [list]:
                - id (inputControl uri)
                - name
                - type
                - label
                - description
        '''
        req = createRequest(
            uriString=uri, 
            wsType='reportUnit', 
            operationName='get')
        res = self.client.service.get(req)
        res = res.encode('utf-8')
        ru = ET.fromstring(res).find('resourceDescriptor')
        report = {}
        report['name'] = ru.get('name')
        report['id'] = ru.get('uriString')
        for infotag in ['label','description']:
            try:
                report[infotag] = ru.find(infotag).text
            except AttributeError, e:
                report[infotag] = None
        
        controls = []
        for rd in ru.findall('resourceDescriptor'):
            if rd.get('wsType') == 'inputControl':
                control = {}
                control['id'] = rd.get('uriString')
                control['name'] = rd.get('name')
                control['type'] = self.get_control_type(
                [rp.find('value').text for rp in rd.findall('resourceProperty') if rp.get('name') == 'PROP_INPUTCONTROL_TYPE'][0])
                for infotag in ['label','description']:
                    try:
                        control[infotag] = rd.find(infotag).text
                    except AttributeError, e:
                        control[infotag] = None
                controls.append(control)
        report['controls'] = controls
        return report
            
    
    def get_control_type(self, jasper_type):
        ''' InputControl types:                         Python type
        1   -> Boolean                                  -> bool
        2   -> Single Value                             -> str
        3   -> Single-select List of Values             -> str
        8   -> Single-select List of Values (radio)     -> str
        6   -> Multi-select List of Values              -> list
        10  -> Multi-select List of Values (check box)  -> list
        4   -> Single-select Query                      -> str
        9   -> Single-select Query (radio)              -> str
        7   -> Multi-select Query                       -> list
        11  -> Multi-select Query (check box)           -> list
        '''
        jasper_type = int(jasper_type)
        if jasper_type in [1]:
            return bool
        if jasper_type in [2, 3, 8, 4, 9]:
            return str
        if jasper_type in [6, 10, 7, 11]:
            return list
    
    
    def run(self, uri, output="PDF", params={}):
        """ uri should be report URI on JasperServer
            output may be PDF, JRPRINT, HTML, XLS, XML, CSV and RTF; default PDF
                but JRPRINT is useless, so don't use it
            params may contain parameters as a simple dict for passing to the report
            this method will return a dict containing 'content-type' and 'data'.
        """
        self.client.set_options(retxml=True) # suds does not parse MIME encoded so we cancel it
        req = createRequest(
            arguments={"RUN_OUTPUT_FORMAT" : output},
            uriString = uri,
            wsType = "reportUnit",
            operationName="runReport",
            params=params)
        res = self.client.service.runReport(req)
        self.client.set_options(retxml=False) # temporarily of course
        try :
            data = parseMultipart(res)
            return data
        except NotMultipartError:
            soapelement = ET.fromstring(res)
            jasperres = soapelement.find('{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://axis2.ws.jasperserver.jaspersoft.com}runReportResponse/runReportReturn')
            if jasperres is None: raise UnknownResponse(res)
            jasperelement = ET.fromstring(jasperres.text)
            raise ServerError(", ".join(map(lambda e: '%s: %s'% (e.tag, e.text), list(jasperelement))))

def createRequest(**kwargs):
    r = ET.Element("request")
    r.set("operationName",kwargs.get("operationName", "list"))
    for argName,argValue in kwargs.get("arguments",{}).items():
        ar = ET.SubElement(r,"argument")
        ar.set("name",argName)
        ar.text = argValue
    rd = ET.SubElement(r,"resourceDescriptor")
    rd.set("name","")
    rd.set("wsType",kwargs.get("wsType","folder"))
    rd.set("uriString",kwargs.get("uriString",""))
    l = ET.SubElement(rd,"label")
    l.text = "null"
    for pname,pval in kwargs.get("params",{}).items():
        if type(pval) in (list,tuple):
            for aval in pval:
                p = ET.SubElement(rd,"parameter")
                p.set("name",pname)
                p.set("isListItem","true")
                p.text = aval
        else:
            p = ET.SubElement(rd,"parameter")
            p.set("name",pname)
            p.text = pval
    return ET.tostring(r)

def parseMultipart(res):
    out = []
    srch = re.search(r'----=[^\r\n]*',res)
    if srch is None: raise NotMultipartError()
    boundary = srch.group()
    #print(boundary)
    res = " \n"+res
    res = "Content-Type: multipart/alternative; boundary=%s\n%s" % (boundary, res)
    message = email.message_from_string(res)
    payloads = message.get_payload()
    #print(payloads)
    for i,payload in enumerate(payloads):
        if i > 0:
            attachment = payload
            #print(attachment.items())
            out.append({'content-type': attachment.get_content_type(), 'data': attachment.get_payload(), 
            'content-id': attachment.get('Content-Id')})
    return out

'''if __name__ == "__main__":
    url = 'http://localhost:8080/jasperserver/services/repository?wsdl'
    j = JasperClient(url,'jasperadmin','jasperadmin')
    a = j.runReport('/reports/samples/AllAccounts',"PDF")
    f = file('AllAccounts.pdf','w')
    f.write(a['data'])
    f.close()'''
