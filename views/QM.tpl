%include( "Head.tpl", title="QM Jobs Monitor")
<script type="text/JavaScript">
<!--
function timedRefresh(timeoutPeriod) {    setTimeout("location.reload(true);",timeoutPeriod);    }
//   -->
</script>
</head>
<body onload="JavaScript:timedRefresh({{1000*refresh}});" >
<p><i>determined at {{now}}</i> - <em>This page will refresh automatically every {{refresh}} seconds.</em></p>

<H1 style="color:#000">Monitoring jobs on QM server</H1>
<p> <b>QM</b> is a simplistic Queue Manager. put your jobs into folders, drop the folders in the queue, and the jobs will be executed sequentially.</p>
<p>Find some documentation <a href="https://github.com/delsuc/QM/blob/master/README.md">HERE</a></p>
    
<div id="container">
<hr>
<h2>Queuing Jobs</h2>

%if waiting:
    <table CELLPADDING=5>
    <tr>
        <th>Name</th>
        %if display_details:
            <th>Action</th>
        %end
        <th>Nb Proc</th>
        <th>Size</th>
        <th>Description</th>
        <th>Owner</th>
    </tr>
    %for i in waiting:
        <tr>
            <td><b>{{i.name}}</b></td>
            %if display_details:
                <td> <center>
                    <a href="/QM_qJobs/{{i.name}}/">view</a>
                    %if delete_jobs:
                        <a href="/delete/QM_qJobs/{{i.name}}">delete</a>
                    %end
                </center></td>
            %end
            <td>{{i.nb_proc}}</td>
            <td>{{i.size}}</td>
            <td>{{i.info}}</td>
            <td>{{i.e_mail}}</td>
            <td>Submitted at: {{i.nicedate}}</td>
        </tr>
    %end
    </table>
%else:
        <P>None</p>
%end
</td>
<hr>
<h2>Running Jobs</h2>
<p>Current Load <br/>
    <i>{{load}}</i></p>
<td>
%if runnings:
    <table CELLPADDING=5>
    <tr><th>Name</th><th>Progress</th>
        %if licence_to_kill:
            <th>Action</th>
        %end
        <th>Nb Proc</th>
        <th>Size</th>
        <th>Description</th>
        <th>Owner</th>
    </tr>
    %for running in runnings:
        <tr><td><b>{{running.name}}</b></td>
        <td>
            <div style="background-color:#EEE; width:100px;">
            <div style="background-color:#0E0; width:{{running.avancement()}}px;">
                &nbsp;
            </div>
            </div>
        </td>
        %if licence_to_kill:
            <td><a href="/kill/{{running.name}}">KILL</a></td>
        %end
        <td>{{running.nb_proc}}</td>
        <td>{{running.size}}</td>
        <td>{{running.info}}</td>
        <td>{{running.e_mail}}</td>
        <td>Started at: {{running.started}}</td>
        </tr>
    %end
    </table>
%else:
    <p>None</p>
%end
</td>
<hr>
<h2>Done Jobs</h2>

<table CELLPADDING=5>
<tr>
    <th>Name</th>
    %if display_details:
        <th>zip file</th>
        <th>Action</th>
    %end
    <th>Duration</th>
    <th>Size</th>
    <th>Owner</th>
    <th>Date</th>
</tr>

%for i in done:
    <tr>
        <td><b>{{i.name}}</b></td>
        %if display_details:
            <td> <a href="/download/{{i.name}}">download</a></td>
            <td> <center>
                <a href="/QM_dJobs/{{i.name}}/">view</a>
                %if delete_jobs:
                    <a href="/delete/QM_dJobs/{{i.name}}">delete</a>
                %end
            </center></td>
        %end
        <td>{{i.time()}}sec</td>
        <td>{{i.size}}</td>
        <td>{{i.e_mail}}</td>
        <td>{{i.nicedate}}</td>
    </tr>
%end
</table>
</td>
<hr>
</div>
</body>
</html>
