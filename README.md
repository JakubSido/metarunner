# Setup conda env 
conda create -n "py310" python=3.10
conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia

# Github tokens
https://github.com/settings/tokens
git clone https://ghp_FwYio....ofAUFSYw2Azios@github.com/CaptainTrojan/LightZero.git



# SSH for windows
## Putty
Putty používá vlastní agent .. pagent
potom je možné pro každé conection nastavit forward agenta

upravit exe pagent.exe a přidat defaultní cestu ke klíči 

potom přiad to 
je možné ho nastartovat se startem pomoci 
win+R shell:startup 

https://docs.unity3d.com/Manual/upm-config-ssh-git-putty.html


## VSCode
VSCode používá ssh-agent ze systému včetně configu z .ssh/config 

Host skirit.ics.muni.cz
    ForwardAgent yes
    HostName skirit.ics.muni.cz
    User sidoj


Start-Service ssh-agent
Set-Service ssh-agent -StartupType Automatic
ssh-add -l

