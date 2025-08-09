// import { FaCheck, FaExclamationTriangle, FaTimes } from "react-icons/fa";

// const StatusBadge = ({ status, goodText, badText, isWarning = false }) => {
//   const getBadgeClass = () => {
//     if (status) {
//       return "bg-success text-success-foreground";
//     } else {
//       return isWarning
//         ? "bg-warning text-warning-foreground"
//         : "bg-destructive text-destructive-foreground";
//     }
//   };

//   const getIcon = () => {
//     if (status) {
//       return <FaCheck className="mr-1.5" />;
//     } else if (isWarning) {
//       return <FaExclamationTriangle className="mr-1.5" />;
//     } else {
//       return <FaTimes className="mr-1.5" />;
//     }
//   };

//   return (
//     <span
//       className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getBadgeClass()}`}
//     >
//       {getIcon()}
//       {status ? goodText : badText}
//     </span>
//   );
// };

// export default StatusBadge;

import { FaCheck, FaExclamationTriangle, FaTimes } from "react-icons/fa";

const StatusBadge = ({ status, goodText, badText, isWarning = false }) => {
  const getBadgeClass = () => {
    if (status) {
      return "bg-green-600 text-white";
    } else {
      return isWarning
        ? "bg-yellow-500 text-gray-900"
        : "bg-red-600 text-white";
    }
  };

  const getIcon = () => {
    if (status) {
      return <FaCheck className="mr-1.5" />;
    } else if (isWarning) {
      return <FaExclamationTriangle className="mr-1.5" />;
    } else {
      return <FaTimes className="mr-1.5" />;
    }
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getBadgeClass()}`}
    >
      {getIcon()}
      {status ? goodText : badText}
    </span>
  );
};

export default StatusBadge;
