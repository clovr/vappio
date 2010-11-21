qname                 exec.q
hostlist              NONE
seq_no                0
load_thresholds       NONE 
suspend_thresholds    NONE
nsuspend              1
suspend_interval      00:05:00
priority              0
min_cpu_interval      00:05:00
processors            UNDEFINED
qtype                 BATCH INTERACTIVE
ckpt_list             NONE
pe_list               make
rerun                 TRUE 
slots                 1  
tmpdir                /tmp
shell                 /bin/bash
prolog                /opt/vappio-scripts/sge/prolog $host $job_owner $job_id $job_name $queue
epilog                /opt/vappio-scripts/sge/epilog $host $job_owner $job_id $job_name $queue 
shell_start_mode      unix_behavior
starter_method        NONE
suspend_method        /opt/vappio-scripts/sge/suspend $host $job_owner $job_id $job_name $queue 
resume_method         /opt/vappio-scripts/sge/resume $host $job_owner $job_id $job_name $queue 
terminate_method      NONE
notify                00:00:60
owner_list            NONE
user_lists            NONE
xuser_lists           NONE
subordinate_list      NONE
complex_values        NONE
projects              NONE
xprojects             NONE
calendar              NONE
initial_state         default
s_rt                  INFINITY
h_rt                  INFINITY
s_cpu                 INFINITY
h_cpu                 INFINITY
s_fsize               INFINITY
h_fsize               INFINITY
s_data                INFINITY
h_data                INFINITY
s_stack               INFINITY
h_stack               INFINITY
s_core                INFINITY
h_core                INFINITY
s_rss                 INFINITY
h_rss                 INFINITY
s_vmem                INFINITY
h_vmem                INFINITY
