- Download Ubuntu Desktop ISO image  
	- https://ubuntu.com/download/desktop  
	- Not sure if it would be better to download [Ubuntu Server](https://ubuntu.com/download/server) (?)  
	- 22.04.1 LTS  
-  
- Install VirtualBox  
	- https://www.virtualbox.org/  
- Create a new virtual machine  
	- **M**achine - > **N**ew...  
		- **N**ame:  
			- CRA-messaging  
			- CRA-database  
			- CRA-backend  
			- CRA-frontend  
		- **I**SO Image: ubuntu-22.04.1-desktop-amd64.iso file downloaded above  
		- **N**ext  
		- Pass**w**ord and **R**epeat Password:  
		- Check Gu**e**st Additions  
		- **N**ext  
		- Base **M**emory: 4096 MB  
		- **P**rocessors: 2  
		- **N**ext  
		- D**i**sk Size: 100 GB  
		- **N**ext  
		- **F**inish  
		- Wait without touching for a long time until you see vboxuser in the middle of the virtual machine screen.  
		- Log in as vboxuser using the password from above.  
-  
- Add vboxuser to sudo  
	- In Terminal:  
	  ```
	  	  su -
	  	  sudo adduser vboxuser sudo
	  	  exit
	  ```
	- Restart virtual machine  
-  
- Install Guest Additions (if didn't check Guest Additions when creating new virtual machine)  
	- Devices -> Insert Guest Additions CD image...  
	- In Terminal:  
	  ```
	  	  cd /media
	  	  cd vboxuser
	  	  cd VBOX_GA*
	  	  sudo ./VBoxLinuxAdditions.run
	  ```
	- Restart virtual machine  
	- View -> Virtual Screen 1 -> (It's nice to have a giant monitor.)  
-  
- Install Git  
	- In Terminal:  
	  ```
	  	  sudo apt update
	  	  sudo apt upgrade
	  	  sudo apt install git
	  ```
	  Answer Yes if asked "Do you want to continue?"  
-  