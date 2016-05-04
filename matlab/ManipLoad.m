function manip = LoadManip(SessionName)
% function LoadManip(SessionName)
%
% This function loads a saved pymanip session and
% returns a structure
%

manip.filename = [SessionName '.hdf5'];
disp(['Loading saved session from file ' manip.filename])

% Logged variables
dset_time = h5read(manip.filename, '/time');
total_size = numel(dset_time);
if (total_size > 0)
    manip.start_date = datetime(dset_time(1), 'ConvertFrom', 'posixtime' );
    manip.end_date = datetime(dset_time(total_size), 'ConvertFrom', 'posixtime' );
    disp(['*** Start: ' datestr(manip.start_date)])
    disp(['***   End: ' datestr(manip.end_date)])
end

info_var = h5info(manip.filename, '/variables');
num_var = numel(info_var.Datasets);
if (num_var > 0)
    disp([num2str(num_var) ' logged variables:'])
    for i=1:num_var
        data = h5read(manip.filename, ['/variables/' info_var.Datasets(i).Name]);
        eval(['manip.' info_var.Datasets(i).Name '=data;'])
    end
end

% Logged datasets
try
    info_data = h5info(manip.filename, '/datasets');
    num_data = numel(info_data.Datasets);
    if num_data > 0
        timestamp = h5readatt(manip.filename, '/datasets', 'timestamp');
        manip.datestamp = datetime(timestamp, 'ConvertFrom', 'posixtime' );
        for i=1:num_data
            data = h5read(manip.filename, ['/datasets/' info_data.Datasets(i).Name]);
            eval(['manip.' info_data.Datasets(i).Name '=data;'])
        end
    end
catch
  % has_data = 0;
end

% Logged parameters
info = h5info(manip.filename);
num_attr = numel(info.Attributes);
if num_attr > 1
    % On ne compte pas email_lastSent
    for i=1:num_attr
        name = info.Attributes(i).Name;
        value = info.Attributes(i).Value;
        eval(['manip.' name '=value;']);
    end
end

end