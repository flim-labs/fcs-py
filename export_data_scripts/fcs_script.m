file_path = '<FILE-PATH>';

% Channel custom names
channel_names_json = '<CHANNEL-NAMES-JSON>';
channel_names = jsondecode(channel_names_json);

% Open the file
metadata = struct('enabled_channels', [], 'correlations', [], 'num_acquisitions', [], 'acquisition_time', [], 'bin_width', [], 'notes', []);

fid = fopen(file_path, 'rb');

if fid == -1
    error('Unable to open the file');
end


% First 4 bytes must be FCS1
first_bytes = fread(fid, 4, 'char')';

if ~isequal(first_bytes, 'FCS1')
    fprintf('Invalid data file');
    fclose(fid);
    return;
end

% Read metadata json length
json_metadata_length = fread(fid, 1, 'uint32');

% Read metadata from file
json_metadata_data = fread(fid, json_metadata_length, 'char')';
json_metadata_str = char(json_metadata_data);
metadata = jsondecode(json_metadata_str);

% Read g2_correlations JSON length
g2_correlations_json_length = fread(fid, 1, 'uint32');

% Extract lag_index and g2_correlations from JSON
g2_correlations_json_data = fread(fid, g2_correlations_json_length, 'char')';
g2_correlations_json_str = char(g2_correlations_json_data);
g2_correlations_json = jsondecode(g2_correlations_json_str);

lag_index = g2_correlations_json.lag_index;
g2_correlations = g2_correlations_json.g2_correlations;

% Function to get channel name
function name = get_channel_name(channel_id, channel_names, truncate_len)
    if nargin < 3
        truncate_len = 5;
    end
    field_name = ['x' num2str(channel_id)];
    if isfield(channel_names, field_name)
        custom_name = channel_names.(field_name);
        if length(custom_name) > truncate_len
            custom_name = [custom_name(1:truncate_len) '...'];
        end
        name = [custom_name ' (Ch' num2str(channel_id + 1) ')'];
    else
        name = ['Channel ' num2str(channel_id + 1)];
    end
end

% Enabled channels
if ~isempty(metadata.enabled_channels)
    channel_names_str = arrayfun(@(ch) get_channel_name(ch, channel_names, 5), metadata.enabled_channels, 'UniformOutput', false);
    disp(['Enabled channels: ' strjoin(channel_names_str, ', ')]);
end

% Correlations (info about correlated channels)
if ~isempty(metadata.correlations)
    correlated_channels = metadata.correlations + 1;
    disp(['Channels correlations: ']);
    disp(mat2str(correlated_channels));
end

% Number of acquisitions
if ~isempty(metadata.num_acquisitions)
    disp(['Number of acquisitions: ' num2str(metadata.num_acquisitions)]);
end

% Acquisition time (duration of the acquisition)
if ~isempty(metadata.acquisition_time)
    num_acquisitions = metadata.num_acquisitions;
    if ~isempty(num_acquisitions)
        disp(['Acquisition time: ' num2str(sprintf('%.2f', metadata.acquisition_time / 1000 / num_acquisitions)) 's']);
    end
end

% Bin width
if ~isempty(metadata.bin_width)
    disp(['Bin width: ' num2str(metadata.bin_width) ' us']);
end

% Tau
disp(['Tau (lag index): ' mat2str(lag_index)]);

% Notes
if ~isempty(metadata.notes)
    disp(['Notes: ' num2str(metadata.notes)]);
end


% Parse correlations data
g2_with_mean = cell(size(g2_correlations, 1), 1);
for idx = 1:size(g2_correlations, 1)
    corr = g2_correlations{idx};
    correlations_mean = corr{2}(1, :);
    g2_vectors = corr{2}(2:end, :); 
    g2_vector_cells = num2cell(g2_vectors, 2);
    g2_with_mean{idx} = {corr{1}, correlations_mean, g2_vector_cells}; 
end

% Plot G(t) correlations
num_plots = numel(g2_with_mean);
num_plots_per_row = 1;
if num_plots < 2
    num_plots_per_row = 1;
elseif num_plots > 1 && num_plots < 4
    num_plots_per_row = 2;
elseif num_plots >= 4
    num_plots_per_row = 4;
end
if num_plots >= 12
    num_plots_per_row = 6;
end

num_rows = ceil(num_plots / num_plots_per_row);

fig = figure('Name', 'Fluorescence Spectroscopy Correlations');
lag_index_plot = lag_index + 1e-6;

for i = 1:num_plots
    corr = g2_with_mean{i};
    channel_info = corr{1};
    channel1 = channel_info(1);
    channel2 = channel_info(2);
    correlations_mean = corr{2};  
    single_gt_correlations = corr{3};  

    ax = subplot(num_rows, num_plots_per_row, i);
    
    % Plot correlations mean
    plot(lag_index_plot, correlations_mean, 'DisplayName', 'G(\tau) mean');
    hold on;

    % Plot single gt correlations vectors
    for data_index = 1:numel(single_gt_correlations)
        current_data = single_gt_correlations{data_index};
        plot(lag_index_plot, current_data, 'DisplayName', ['G(\tau) ' num2str(data_index)]);
    end
   
    ch1_name = get_channel_name(channel1, channel_names, 5);
    ch2_name = get_channel_name(channel2, channel_names, 5);
    
    hold off;
    set(gca, 'XScale', 'log');
    xlim([1, max(lag_index_plot)]);
    xlabel('\tau (\mus)');
    ylabel('G(\tau)');
    title([ch1_name ' - ' ch2_name]);
    grid on;
    legend('Location', 'northeast');
end

hold off;