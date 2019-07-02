
files = dir('_data/*.csv');
for file = files'
    fileFullPath = sprintf('%s/%s', file.folder,file.name);
    [filepath,name,ext] = fileparts(fileFullPath);
    
    tmp = trackingRead(fileFullPath);
    tmp.frame=tmp.frame/24;

    height = 290
    width = 450
    xCutOff = 50
    yCutOff = 0.10
    textSize = 16
    yTicks = [0 0.02 0.04 0.06 0.08 0.1]
    exponent = -2

    if contains(name,'dram')
        width = 730
        textSize = 20
    end

    if contains(name,'l2')
        width = 730
        textSize = 22
    end

    if contains(name,'Motivation')
        xCutOff = 17
        textSize = 18
        
        height = 220
        width = 470

        yCutOff = 0.14
        yTicks = [0 0.03 0.06 0.09 0.12]

        if contains(name,'E-5')
            yCutOff = 0.008
            yTicks = [0 0.002 0.004 0.006 0.008 0.01]
            exponent=-3
        end
    end

    createTrackingFigure(tmp.frame, tmp.score, tmp.target, xCutOff, yCutOff, height, width, textSize, yTicks, exponent)
    h= gcf
    set(h,'Units','Inches');
    pos = get(h,'Position');
    set(h,'PaperPositionMode','Auto','PaperUnits','Inches','PaperSize',[pos(3)-0.1, pos(4)+0.1])
    
    outputFileName = sprintf('%s/%s.pdf', file.folder,name);
    print(h,outputFileName,'-dpdf','-r0')

end

quit