import StatusBadge from "./StatusBadge.jsx";

const MachineList = ({ machines, onSort, sortConfig }) => {
  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th
                className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition"
                onClick={() => onSort("machine_id")}
              >
                <div className="flex items-center">
                  Machine ID
                  {sortConfig.key === "machine_id" && (
                    <span>{sortConfig.direction === "asc" ? "↑" : "↓"}</span>
                  )}
                </div>
              </th>
              <th
                className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition"
                onClick={() => onSort("last_checkin")}
              >
                <div className="flex items-center">
                  Last Check-in
                  {sortConfig.key === "last_checkin" && (
                    <span>{sortConfig.direction === "asc" ? "↑" : "↓"}</span>
                  )}
                </div>
              </th>
              <th className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Disk Encryption
              </th>
              <th className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                OS Updates
              </th>
              <th className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Antivirus
              </th>
              <th className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sleep Settings
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {machines.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  No machines found
                </td>
              </tr>
            ) : (
              machines.map((machine) => (
                <tr key={machine.machine_id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 max-w-[150px] truncate sm:max-w-xs">
                      {machine.machine_id}
                    </div>
                  </td>
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(machine.last_checkin * 1000).toLocaleString()}
                    </div>
                  </td>
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <StatusBadge
                      status={machine.disk_encryption}
                      goodText="Encrypted"
                      badText="Unencrypted"
                    />
                  </td>
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <StatusBadge
                      status={!machine.os_updates}
                      goodText="Updated"
                      badText="Update Available"
                      isWarning={true}
                    />
                  </td>
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <StatusBadge
                      status={machine.antivirus}
                      goodText="Active"
                      badText="Inactive"
                    />
                  </td>
                  <td className="px-4 py-4 sm:px-6 whitespace-nowrap">
                    <StatusBadge
                      status={machine.sleep_settings}
                      goodText="≤10 min"
                      badText=">10 min"
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MachineList;
