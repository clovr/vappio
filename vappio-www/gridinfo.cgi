#!/usr/bin/perl

use strict;

use JSON;
use CGI qw(:standard);
use DateTime;
use Date::Manip; 

my $date=ParseDate("now");
#can limit the update of the status to every X minutes
#run on each request for now
`/opt/vappio-scripts/gridstatus.sh`;
#
#read status files
open SGESTATUS, "/var/vappio_runtime/sgestatus.txt";
open EC2STATUS, "/var/vappio_runtime/ec2status.txt";
my @sgestatus = <SGESTATUS>;
my @ec2status = <EC2STATUS>;

my @status;
my $hosts = {};

my $id;

foreach my $l (@ec2status){
	chomp $l;
	my ($publicip,$privateip, $status, $type, $time) = split(/\t/,$l);
	if($status eq 'pending'){
		$privateip = $id++;
    }
	if($privateip){
		$hosts->{$privateip}->{'privateip'} = $privateip; 
		$hosts->{$privateip}->{'publicip'} = $publicip; 
		$hosts->{$privateip}->{'status'} = $status; 
		$hosts->{$privateip}->{'type'} = $type;
		$hosts->{$privateip}->{'time'} = $time; 
	}
}
foreach my $l (@sgestatus){
       chomp $l;
        my ($ip,$role, $queue, $idle, $job, $load, $memtot, $memused, $cpus) = split(/\t/,$l);
    #    my $privateip = `nslookup $ip | grep Name`;
	#($privateip) = ($privateip =~ /Name:\s+(.*)/);
	my $privateip;
	if($privateip eq ''){
			if(exists $hosts->{"$ip.ec2.internal"}){ $privateip = "$ip.ec2.internal";}
			elsif(exists $hosts->{"$ip.compute-1.internal"}){$privateip = "$ip.compute-1.internal";}
	}
    $hosts->{$privateip}->{'load'} = $load;
    $hosts->{$privateip}->{'role'} = $role;
    $hosts->{$privateip}->{'type'} =  $hosts->{$privateip}->{'type'};
    $hosts->{$privateip}->{'memtot'} = $memtot;
    $hosts->{$privateip}->{'memused'} = $memused;
    $hosts->{$privateip}->{'cpus'} = $cpus;
	$hosts->{$privateip}->{'queues'}->{$queue}++;
	if($queue eq 'exec.q'){
		if($idle eq 'idle'){
			$hosts->{$privateip}->{'eidle'}++;
		}
		else{	
			$hosts->{$privateip}->{'ebusy'}++;
		}
	}
	else{
		if($idle eq 'idle'){        
            $hosts->{$privateip}->{'didle'}++;
        }
       elsif($idle eq 'epending'){
            $hosts->{$privateip}->{'epending'}++;

        } elsif($idle eq 'dpending'){
			$hosts->{$privateip}->{'dpending'}++;
		
		}
		else{
            $hosts->{$privateip}->{'dbusy'}++;
        }
	}
	$hosts->{$privateip}->{'slots'}++;
} 
my @status;

foreach my $privateip (keys %$hosts){
	push @status,{'privateip'=>"<a href='/ganglia/?h=$hosts->{$privateip}->{'privateip'}&c=Grid+V1'>$hosts->{$privateip}->{'privateip'}</a>",
				  'publicip'=>$hosts->{$privateip}->{'publicip'},
				  'status'=>$hosts->{$privateip}->{'status'},
				  'role'=>$hosts->{$privateip}->{'role'},
				  'type'=>$hosts->{$privateip}->{'type'},
				  'uptime'=>Delta_Format(DateCalc(ParseDate($hosts->{$privateip}->{'time'}),ParseDate("now")),1,"%ht hours"),
				  'load'=>$hosts->{$privateip}->{'load'},
	  				'memtot'=>$hosts->{$privateip}->{'memtot'},
					'memused'=>$hosts->{$privateip}->{'memused'},
					'cpus'=>$hosts->{$privateip}->{'cpus'},
					'slots'=>$hosts->{$privateip}->{'slots'},
					'eidle'=>$hosts->{$privateip}->{'eidle'}||0,
					'ebusy'=>$hosts->{$privateip}->{'ebusy'}||0,
					'epending'=>$hosts->{$privateip}->{'epending'},
					'dbusy'=>$hosts->{$privateip}->{'dbusy'}||0,
					'didle'=>$hosts->{$privateip}->{'didle'}||0,
					'dpending'=>$hosts->{$privateip}->{'dpending'}
					} if($hosts->{$privateip}->{'role'} || $hosts->{$privateip}->{'status'} eq 'pending');
}	

print header('application/x-json');
my $coder = JSON::PP->new->allow_nonref;
#$coder->canonical(1);
print $coder->encode (\@status);

exit;

