#!/bin/bash

function checkStatus(){
	local SimStatusFileName=$(ls *-Status.txt)
	local iCount=0
  
	while read fileline
	do
		local CheckError=$(echo $fileline | awk -F. '{split($1,a,"::"); print a[1]}')
		if [ "$CheckError" = "Error" ]
		then
			iCount=`expr $iCount + 1`
		fi
	done < $SimStatusFileName
  
	return $iCount
}

CurrentDir=$(pwd)
PythonPath="/usr/bin/python"
Python3Path="/home/APP/anaconda3/bin/python"
LSFPythonPath="/home/LSF/scripts/python_sub"
ISLMCmdPath="/home/fiper/ISLM/ISLMCommands"
SMARTPCIPath="/home/fiper/ISLM/ISLMCommands/SART/SMART"
AbqViewerPath="/home/APP/Abaqus2017/Commands/abaqus viewer"
ATCModalFlatspot="/home/users/fiper/ISLM/ISLMCommands/SART/Static/Static_Modal_Flatspot"
ATCStaticStiffness="/home/users/fiper/ISLM/ISLMCommands/SART/Static/Static_Stiffness"
DOEPath="/home/users/fiper/ISLM/ISLMCommands/SART/DOE"
EndurancePath="/home/users/fiper/ISLM/ISLMCommands/SART/Static/Static_Endurance_02"
export LM_LICENSE_FILE=27003@fileserver01
source /home/fiper/.bash_profile

echo "********** Start Simulation Process **********"
date
echo "**********************************************"
$PythonPath $SMARTPCIPath/Pre3DModelGeneration.py
$PythonPath $SMARTPCIPath/ISLMCopy2DMeshImage.py
$PythonPath $ISLMCmdPath/SART/Static/PreABAQUSInpGeneration.py
$PythonPath $ISLMCmdPath/SART/Static/ISLMCheckStaticJobStatus.py 100
checkStatus
StatusValue=$?
if [ $StatusValue -eq 0 ]
then
    $PythonPath /home/users/fiper/Desktop/Documents/KJG/SMART_PersonalUse_script/RunStaticSART_v2_0_buffingTire.py
    $PythonPath $ISLMCmdPath/SART/Static/ISLMCheckStaticJobStatus.py 200
    checkStatus
    StatusValue=$?
    if [ $StatusValue -eq 0 ]
    then
        $PythonPath $EndurancePath/auto_ISLM.py
        if [ $(echo $(lmstat -a -c 27003@10.82.66.82 |grep 'Users of viewer' | awk '{ printf($6-$11); }')) -ne 0 ]; then
            echo "### PostLongTermEndurance.py / ABQ Viewer LIC OK ###"
            /home/APP/Abaqus2017/CAE/linux_a64/code/bin/ABQLauncher viewer noGUI=$ISLMCmdPath/SART/Static/PostLongTermEndurance.py
        else
            echo "### PostLongTermEndurance.py / There is no ABQ Viewer LIC ###"
            while [ $(echo $(lmstat -a -c 27003@10.82.66.82 |grep 'Users of viewer' | awk '{ printf($6-$11); }')) -eq 0 ]; do
                sleep 31
                echo "LIC Check"
            done
            /home/APP/Abaqus2017/CAE/linux_a64/code/bin/ABQLauncher viewer noGUI=$ISLMCmdPath/SART/Static/PostLongTermEndurance.py
        fi
        $PythonPath $ISLMCmdPath/SART/Static/PostLongTermEnduranceSubPlot.py
        $PythonPath $ISLMCmdPath/SART/Static/ISLMCheckStaticJobStatus.py 300
        $PythonPath $ISLMCmdPath/SART/Static/ISLMExtractStaticResult.py
        # $PythonPath $ISLMCmdPath/Execution/ISLMDeleteSuccessJobFiles.py
    fi
fi
$PythonPath $ISLMCmdPath/SART/Static/ISLMManageStaticLifecycle.py JobComplete
checkStatus
StatusValue=$?
if [ $StatusValue -ne 0 ]
then
    $PythonPath $ISLMCmdPath/Execution/ISLMExtractError.py
fi
echo "********** End Simulation Process **********"
date
echo "********************************************"
exit