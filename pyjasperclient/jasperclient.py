try:
    from xml.etree import ElementTree as ET
except ImportError, e:
    from elementtree import ElementTree as ET
from suds.client import Client
import email,re

class JasperClient:
    def __init__(self,url,username,password):
        self.client = Client(url,username=username,password=password)

    def listReports(self,dir=""):
        """ get a list containing report URIs on JasperServer
        optional dir param shows the directory to list in JasperServer
        """
        req = createRequest(
            uriString=dir, 
            wsType="folder", 
            operationName="list")
        res = self.client.service.list(req)
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
    
    def runReport(self,uri,output="PDF",params={}):
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
        res = parseMultipart(res)
        return res

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
    boundary = re.search(r'----=[^\r\n]*',res).group()
    res = " \n"+res
    res = "Content-Type: multipart/alternative; boundary=%s\n%s" % (boundary, res)
    message = email.message_from_string(res)
    attachment = message.get_payload()[1]
    return {'content-type': attachment.get_content_type(), 'data': attachment.get_payload()}

if __name__ == "__main__":
    url = 'http://localhost:8080/jasperserver/services/repository?wsdl'
    j = JasperClient(url,'jasperadmin','jasperadmin')
    a = j.runReport('/reports/AllAccounts',"PDF")
    f = file('AllAccounts.pdf','w')
    f.write(a['data'])
    f.close()
