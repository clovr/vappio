# ~/.profile: executed by Bourne-compatible login shells.

if [ "$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi

mesg n
if [ -f "$vappio_runtime/node_type" ]; then
    nodetype=`cat $vappio_runtime/node_type`;
else  
    nodetype="OFFLINE"
fi
ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`

echo "###README###"
echo "Access the CloVR appliance from a web browser at http://$ipaddr"

if [ "$SCREENME" ]; then
    screen -list | grep clovr-login
    if [ "$?" == "0" ]; then
	exec screen -rd clovr-login	
    else
	exec screen -S clovr-login startup_msg.sh
    fi
fi

