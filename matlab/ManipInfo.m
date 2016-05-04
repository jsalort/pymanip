function ManipInfo(SessionName)
% function ManipInfo(SessionName)
%
% Returns information on a pymanip saved session.
%

filename = [SessionName '.hdf5'];
disp(['Loading saved session from file ' filename])

% Logged variables
dset_time = h5read(filename, '/time');
total_size = numel(dset_time);
if (total_size > 0)
	start_date = datetime(dset_time(1), 'ConvertFrom', 'posixtime' );
	end_date = datetime(dset_time(total_size), 'ConvertFrom', 'posixtime' );
	disp(['*** Start: ' datestr(start_date)])
	disp(['***   End: ' datestr(end_date)])
end

info_var = h5info(filename, '/variables');
num_var = numel(info_var.Datasets);
if (num_var > 0)
	disp([num2str(num_var) ' logged variables:'])
	for i=1:num_var
		disp(['  ' info_var.Datasets(i).Name])
	end
end

% Logged datasets
try
	info_data = h5info(filename, '/datasets');
	num_data = numel(info_data.Datasets);
	if num_data > 0
		timestamp = h5readatt(filename, '/datasets', 'timestamp');
		datestamp = datetime(timestamp, 'ConvertFrom', 'posixtime' );
		disp(['*** Dataset timestamp: ' datestr(datestamp)])
		disp([num2str(num_data) ' logged datasets'])
		for i=1:num_data
			disp(['  ' info_data.Datasets(i).Name])
		end
	end
catch
	has_data = 0;
end

% Logged parameters
info = h5info(filename);
num_attr = numel(info.Attributes);
if num_attr > 1
	% On ne compte pas email_lastSent
	disp([num2str(num_attr-1) ' logged parameters'])
	for i=1:num_attr
		name = info.Attributes(i).Name;
		value = info.Attributes(i).Value;
		if strcmp(name, 'email_lastSent') == 0
			disp(['  ' name ' = ' num2str(value)])
		end
	end
end

end