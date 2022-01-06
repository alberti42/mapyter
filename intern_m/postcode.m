global Gc8i96uVM
Gc8i96uVM_cs = get(groot,'children');
if ~isempty(Gc8i96uVM_cs)
    if ~isempty(Gc8i96uVM.newfigs)
        Gc8i96uVM_cs = setdiff(Gc8i96uVM_cs,[Gc8i96uVM.newfigs.fig]);
    end
    Gc8i96uVM_cs=Gc8i96uVM_cs(:).';
    for Gc8i96uVM_c = Gc8i96uVM_cs
        set(groot,'CurrentFigure',Gc8i96uVM_c);
        drawnow
    end
    builtin('clear','Gc8i96uVM_c');
    if ~isempty(Gc8i96uVM.newfigs)
        close([Gc8i96uVM.newfigs.fig]);
    end
end
Gc8i96uVM.builtin=true;
builtin('clear','Gc8i96uVM','Gc8i96uVM_cs');