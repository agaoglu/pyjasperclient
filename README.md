Introduction
============

A simple python module to run and get generated reports deployed on a JasperServer. Module works by consuming the SOAP web service provided by the JasperServer. It is ideal for python projects that uses JasperServer for reporting and needs a way to access/publish these reports to their users easily. However, this project is not a management interface for JasperServer, you should use its web interface and/or iReport for that.

Requirements
------------

* re # included in standard distribution
* email # included in standard distribution
* xml # included in standard distribution
* suds (>= 0.3.8 GA) # https://fedorahosted.org/suds/wiki

NOTE: module has been tested on python v2.6.4 only.

Usage
=====

For the impatient
-----------------

    from jasperclient import JasperClient
    
    url = 'http://localhost:8080/jasperserver/services/repository?wsdl'
    j = JasperClient(url,'joeuser','joeuser')
    ret = j.runReport('/reports/samples/AllAccounts',"PDF")
    f = file('AllAccounts.pdf','w')
    f.write(ret['data'])
    f.close()


JasperClient object
-------------------
Create your Jasper object with JasperServer wsdl url and JasperServer credentials.

    j = JasperClient( 'http://localhost:8080/jasperserver/services/repository?wsdl', 'joeuser', 'joeuser')

There are only two methods that can be used.

    JasperClient.listReports(dir="")

Returns a list of strings that are report URIs of the JasperServer. Optional dir param may be used to define the directory to look for. It should start with / and end with directory name. (No / at the end)

    Jasper.runReport(uri,output="PDF",params={})

This will run the report for the URI given in uri and generate a dict containing 'content-type' and 'data'. 'content-type' can be used to send as an HTTP response header. params is a simple dict to pass directly to the running report.

Check the source for more info
