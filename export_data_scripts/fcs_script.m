file_path = '<FILE-PATH>';

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

% Enabled channels
if ~isempty(metadata.enabled_channels)
    disp(['Enabled channels: ' strjoin(arrayfun(@(ch) ['Channel ' num2str(ch + 1)], metadata.enabled_channels, 'UniformOutput', false), ', ')]);
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


% Calc G(t) correlations mean
g2_with_mean = cell(size(g2_correlations, 1), 1);
for idx = 1:size(g2_correlations, 1)
    corr = g2_correlations{idx};
    g2_vector = corr{2};
    g2_vector_length = size(g2_vector, 1);
    correlations_length = size(g2_vector, 2);
    average = zeros(1, correlations_length);
    for i = 1:g2_vector_length
        for j = 1:correlations_length
            average(j) = average(j) + g2_vector(i, j);
        end
    end
    for k = 1:correlations_length
        average(k) = average(k) / g2_vector_length;
    end
    g2_vector_cells = num2cell(g2_vector, 2);
    g2_with_mean{idx} = {corr{1}, average, g2_vector_cells};
end

% Plot G(t) correlations
num_plots = numel(g2_with_mean);
num_plots_per_row = 1;
if num_plots < 2
    num_plots_per_row = 1;
end
if num_plots > 1 && num_plots < 4
    num_plots_per_row = 2;
end
if num_plots >= 4
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
    average = corr{2};
    data_list = corr{3};
    ax = subplot(num_rows, num_plots_per_row, i);
    for data_index = 1:numel(data_list)
        current_data = data_list{data_index};
        plot(lag_index_plot, current_data, 'DisplayName', ['G(\tau) ' num2str(data_index)]);
        hold on;
    end
    if numel(data_list) > 1
        plot(lag_index_plot, average, 'DisplayName', 'G(\tau) mean');
    end    
    hold off;
    set(gca, 'XScale', 'log');
    xlim([1, max(lag_index_plot)]);
    xlabel('\tau(\mus)');
    ylabel('G(\tau)');
    title(['Channel ' num2str(channel1 + 1) ' - Channel ' num2str(channel2 + 1)]);
    grid on;
    legend('Location', 'northeast');
end

hold off;