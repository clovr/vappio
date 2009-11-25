#!/usr/bin/perl

use strict;
my $SGE_ROOT='/opt/sge';
my $SGE_ROOT_BIN='$SGE_ROOT/bin/lx24-x86/';
$ENV{'SGE_ROOT'}="$SGE_ROOT";

my @lines=`$SGE_ROOT_BIN/qhost -q -j`;

my $master = `cat $SGE_ROOT/default/common/act_qmaster`; 

#HOSTNAME                ARCH         NCPU  LOAD  MEMTOT  MEMUSE  SWAPTO  SWAPUS
#-------------------------------------------------------------------------------
#global                  -               -     -       -       -       -       -
#domU-12-31-39-00-48-36  lx24-x86        1  0.00    1.7G  159.2M  896.0M     0.0
#   wf.q                 BIP   0/1      
#   repository.q         BIP   0/1      
#   staging.q            BIP   0/2      
#   stagingsub.q         BIP   0/1      
#   harvesting.q         BIP   0/2      

#$ip $type $queue $idle $job $load $memtot $memused $cpus

my $hosts = {};
my $host;

foreach my $line (@lines){
	chomp $line;
	if($line =~ /^HOSTNAME/ || $line =~ /^\-/ || $line =~ /^global/){
	}	
    if($line =~ /^\S+/){
		my @elts = split(/\s+/,$line);
  		$host=$elts[0];
		$hosts->{$host}->{'cpus'}=$elts[2];
		$hosts->{$host}->{'load'}=$elts[3];
		$hosts->{$host}->{'memtot'}=$elts[4];
		$hosts->{$host}->{'memused'}=$elts[5];
		if($master =~ /$host/){
			$hosts->{$host}->{'role'} = "master";
            my @pending = `$SGE_ROOT_BIN/qstat -u guest -s p | grep RunWork`;
            $hosts->{$host}->{'epending'} = scalar(@pending)-2 if(scalar(@pending));
            my @pending = `$SGE_ROOT_BIN/qstat -u guest -s p | grep -v RunWork`;
            $hosts->{$host}->{'dpending'} = scalar(@pending)-2 if(scalar(@pending));
		}
	}
	elsif($line =~ /^\s+\w+\.q/){
		$line =~ s/^\s+//g;
	  	my @elts = split(/\s+/,$line);
	    my($busy,$total) = ($elts[2] =~ /(\d+)\/(\d+)/);
		$hosts->{$host}->{'queue'}->{$elts[0]}->{'busy'}=$busy;
		$hosts->{$host}->{'queue'}->{$elts[0]}->{'total'}=$total;
		if($elts[0] =~ /^staging.q/ && !exists $hosts->{$host}->{'role'}){
            $hosts->{$host}->{'role'} = "data";
        }
	    if($elts[0] =~ /exec.q/ && !exists $hosts->{$host}->{'role'}){
            $hosts->{$host}->{'role'} = "exec";
        }


	}
}

foreach my $h (keys %$hosts){
	foreach my $q (keys %{$hosts->{$h}->{'queue'}}){
		my $qinfo = $hosts->{$h}->{'queue'}->{$q};
		my $idle = $qinfo->{'total'}-$qinfo->{'busy'};
		for(my $i=0;$i<$idle;$i++){
			print "$h\t$hosts->{$h}->{'role'}\t$q\tidle\tnone\t$hosts->{$h}->{'load'}\t$hosts->{$h}->{'memtot'}\t$hosts->{$h}->{'memused'}\t$hosts->{$h}->{'cpus'}\n";
		}
		for(my $i=0;$i<$qinfo->{'busy'};$i++){
            print "$h\t$hosts->{$h}->{'role'}\t$q\tbusy\tnone\t$hosts->{$h}->{'load'}\t$hosts->{$h}->{'memtot'}\t$hosts->{$h}->{'memused'}\t$hosts->{$h}->{'cpus'}\n";
        }
	}
	for(my $i=0;$i<$hosts->{$h}->{'epending'};$i++){
        print "$h\t$hosts->{$h}->{'role'}\t\tepending\tnone\t$hosts->{$h}->{'load'}\t$hosts->{$h}->{'memtot'}\t$hosts->{$h}->{'memused'}\t$hosts->{$h}->{'cpus'}\n";
    }	
	for(my $i=0;$i<$hosts->{$h}->{'dpending'};$i++){
        print "$h\t$hosts->{$h}->{'role'}\t\tdpending\tnone\t$hosts->{$h}->{'load'}\t$hosts->{$h}->{'memtot'}\t$hosts->{$h}->{'memused'}\t$hosts->{$h}->{'cpus'}\n";
    }
} 
