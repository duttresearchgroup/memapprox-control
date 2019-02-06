
files = dir('_data/*.csv');
for file = files'
    fileFullPath = sprintf('%s/%s', file.folder,file.name);
    [filepath,name,ext] = fileparts(fileFullPath);
    
    tmp = trackingRead(fileFullPath)
    tmp.frame=tmp.frame/24
    createTrackingFigure(tmp.frame, tmp.score, tmp.target, 0.15)
    h= gcf
    set(h,'Units','Inches');
    pos = get(h,'Position');
    set(h,'PaperPositionMode','Auto','PaperUnits','Inches','PaperSize',[pos(3)+0.4, pos(4)+0.4])
    
    outputFileName = sprintf('%s/%s.pdf', file.folder,name);
    print(h,outputFileName,'-dpdf','-r0')

end

quit