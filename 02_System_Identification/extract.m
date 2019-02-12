clearvars
memoryComponent = elasticRead('_data/SI_l1w.csv')

up = memoryComponent.knob;
yp = memoryComponent.score;

mu = mean(up(1:end-1))
my = mean(yp(2:end))

u = up - mu;
y = yp - my;

clearvars memoryComponent up yp 

data = iddata(y, u, 0.33)

np = 2;
nz = 1;
iodelay = NaN;
Ts = 0.33;
sys = tfest(data,np,nz,iodelay,'Ts',Ts);

% sys = tfest(data,np,nz,iodelay,'Ts',Ts);

%double kp=0.00001064;
%double ki=0.0005067;
clearvars my data

% C_pi is a pid controller object that represents a PI controlle
% crossover frequency to 1.0
[C_pi,info] = pidtune(sys,'PI',1)

% Examine the closed-loop step response
% PIC = feedback(sys*C_pi,1);
% 
% subplot(1,2,1);
% rlocus(PIC)
% subplot(1,2,2);
% step(PIC)

kp=C_pi.kp
ki=C_pi.ki

clearvars info PIC sys