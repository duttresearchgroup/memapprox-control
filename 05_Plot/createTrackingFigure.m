function createTrackingFigure(X1, Y1, Y2, xCutOff, yCutOff, height, width, textSize, yTicks, exponent)
%CREATEFIGURE1(X1, YMatrix1)
%  X1:  vector of x data
%  YMATRIX1:  matrix of y data

%  Auto-generated by MATLAB on 25-Nov-2018 18:44:36

% Create figure
figure1 = figure();

% Create axes
axes1 = axes('Parent',figure1);
hold(axes1,'on');

% Create multiple lines using matrix input to plot
plot1 = plot(X1,Y1, X1, Y2);
set(plot1(1),'DisplayName','Observed Score','Color',[0 0.3 0.6],'LineWidth',2);
set(plot1(2),'DisplayName','Target Score','Color',[1 0.25 0.25],'LineWidth',3, 'LineStyle', '--');

% Create ylabel
ylabel({'Score'});

% Create xlabel
xlabel({'Time (in seconds)'});

% Uncomment the following line to preserve the X-limits of the axes
% xlim(axes1,[0 1000]);
% Uncomment the following line to preserve the Y-limits of the axes
% ylim(axes1,[0 0.100000001490116]);
box(axes1,'on');
% Create legend
legend(axes1,'show');

axis([0 xCutOff 0 yCutOff])
ax = gca;
ax.XGrid = 'off';
ax.YGrid = 'on';
ax.YAxis.Exponent = exponent;

set(gca,'FontSize',textSize)

set(gcf,'position',[0,0,width,height])
yticks(yTicks)